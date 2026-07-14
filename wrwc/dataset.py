from datetime import datetime
import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
from functools import partial
from gsw import O2sol
from wrwc.config import PROCESSED_DATA_DIR, RAW_DATA_DIR


def calculate_dissolved_oxygen_saturation(df):
    def _fill_temperature_values(df_wide):
        """
        Interpolate missing temperature
        The sites are grouped by site and month. The missing value are interpolated
        between years at the same site and during the same month. e.g. if
        May 2008 was missing it would use the average between May 2007 and 2009.
        """

        def _interpolate_temperature(group):
            group = group.set_index('year')
            group['Temperature'] = group['Temperature'].interpolate(method='linear')
            return group

        # groupby site and month
        gb_site_month = (
            df_wide
            .reset_index()
            .assign(month=lambda x: x['date'].dt.month,
                    year=lambda x: x['date'].dt.year)
            .groupby(by=['ww_id', 'month'])
        )
        # Interpolate temperature
        df_interp = (
            gb_site_month
            .apply(_interpolate_temperature, include_groups=True)
            .reset_index(drop=True)
            .sort_values(by=['ww_id', 'date'])
        )
        return df_interp

    def _fill_salinity_values(df_wide):
        """
        Fill NA salinity values. Median salinity for brackish site and 0 for freshwater
        """

        m_brackish_sites = df_wide['ww_id'] == 'WW308'
        median_salinity = df_wide.loc[m_brackish_sites, 'Salinity, (ppt)'].median()

        # 1. Fill Brackish Site (WW308) NAs with the median
        df_wide.loc[m_brackish_sites, 'Salinity, (ppt)'] = (
            df_wide.loc[m_brackish_sites, 'Salinity, (ppt)'].fillna(median_salinity))

        # 2. Fill all other NAs (for freshwater sites) with 0
        df_wide.loc[~m_brackish_sites, 'Salinity, (ppt)'] = (
            df_wide.loc[~m_brackish_sites, 'Salinity, (ppt)'].fillna(0.))

        return df_wide

    def _dissolved_oxygen_saturation(df_wide):
        """ Calculates dissovled oxygen saturation """

        # Calculate maximum dissolved oxygen at salinity, pressure, and temperature
        N = len(df_wide)
        df_wide['do_max'] = O2sol(
            SA=df_wide['Salinity, (ppt)'],  # Assumes ppt is close enough to SA in g/kg
            CT=df_wide['Temperature'],
            p=np.repeat(0, N),  # Assume 1 atm
            lat=np.repeat(41.8246, N),  # Providence coordinates
            lon=np.repeat(-71.418884, N),
        ) * (31.998 * 1e-3)  # Convert from umol/kg to mg/l

        # Calculate dissolved oxygen saturation
        df_do_saturation = (
            df_wide
            .assign(do_sat=df_wide['Dissolved Oxygen'] / df_wide['do_max'] * 100,
                    sample_type='Water',
                    depth=0.0,
                    parameter='Dissolved Oxygen Saturation',
                    unit='percent')
            .drop(columns=['Salinity, (ppt)', 'Temperature', 'month', 'Dissolved Oxygen', 'do_max'])
            .rename(columns={'do_sat': 'concentration'})
            .dropna(subset=['concentration'])
            .set_index('date')
        )
        return df_do_saturation

    # Process dataframe for calculations
    m = df['parameter'].isin(['Dissolved Oxygen', 'Temperature', 'Salinity, (ppt)'])
    ...
    df_do = (
        df
        .loc[m, ['ww_id', 'date', 'parameter', 'concentration']]
        .reset_index()
        .pivot_table(
            index=['ww_id', 'date'],
            columns='parameter',
            values='concentration'
        )
    )

    # Fill in missing values
    df_interp = _fill_temperature_values(df_do)
    df_interp = _fill_salinity_values(df_interp)

    # Calculate dissolved oxygen saturation
    df_do_sat = _dissolved_oxygen_saturation(df_interp).reset_index(drop=False)

    # Append calculated values
    df_out = pd.concat([df, df_do_sat], axis=0, ignore_index=False)

    return df_out


def concentration_data(
    input_path: Path = RAW_DATA_DIR / "WoonasquatucketData_through_2024.csv",
    output_path: Path = PROCESSED_DATA_DIR,
):
    """
    Formats the concentration data and fixes inconsistencies in the raw data.

    :param input_path: Path to raw data csv file
    :param output_path: Path to directory to save output
    :return: None
    """
    logger.info("Processing dataset...")

    site_info_path = RAW_DATA_DIR / "SiteInfo.csv"

    # Read in data
    df_data_raw = pd.read_csv(input_path)
    df_data = df_data_raw.copy()
    df_site = pd.read_csv(site_info_path)

    # Standardize column names
    df_data.columns = [col.replace(" ", "_").lower() for col in df_data.columns]

    # Create dictionary of parameter codes to parameter name for relabeling with concise names
    param_code_to_name = {
        s.split("-")[-1].strip(): s.split("-")[0].strip() for s in df_data.parameter.unique()
    }
    shortened_names = {
        "00915": "Calcium",
        "32209": "Chlorophyll a",
        "82903": "Depth",
        "00631": "Nitrate + Nitrite",
        "00930": "Sodium",
        "00600": "Nitrogen, Total",
        "00608": "Nitrogen, Ammonia",
    }
    param_code_to_name.update(shortened_names)

    # Process Site info
    df_site.columns = [col.replace(" ", "_").lower() for col in df_site.columns]
    df_site.rename(columns={"ww_station": "ww_id"}, inplace=True)

    # Process dataframe
    df_data = (
        df_data
        # Create datetime, parameter code, and parameter name columns
        .assign(
            date=pd.to_datetime(df_data["date_of_sample"]),
            param_code=[s.split("-")[-1].strip() for s in df_data["parameter"]],
            unit=df_data["unit"].replace("mg/L", "mg/l"),
        )
        .assign(parameter=lambda x: [param_code_to_name[s] for s in x["param_code"]])
        # Drop no data or redundant columns
        .drop(
            columns=[
                "sediment_particle_size",
                "particle_size_unit",
                "fish_sample_type",
                "fish_taxa",
                "date_of_sample",
            ]
        )
        .merge(
            df_site.loc[:, ["ww_id", "wbid", "wb_type", "site_descr", "lat_dd", "lon_dd"]],
            on="ww_id",
            how="left",
        )
    )

    # Standardize unit for Fecal Coliforms
    df_data.loc[df_data['parameter'] == 'Fecal Coliform', 'unit'] = 'MPN/100ml'

    # Calculate dissolved oxygen concentration
    df_data = calculate_dissolved_oxygen_saturation(df_data)

    logger.success("Processing dataset complete.")

    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"wrwc-processed-data-{date_str}.csv"
    df_data.to_csv(output_path / filename, index=False)


def list_to_string(l: list, wrap: int = 4):
    """
    Converts a list to a string
    :param l: List to convert
    :param wrap: Number of values to fit on a line
    :return: String format of the list
    """
    output_str = ""
    l_strings = [str(s).replace(",", "") for s in l]
    for i, item in enumerate(l_strings):
        output_str += f"{item}"
        if i + 1 != len(l_strings):
            output_str += ", "
            if (i + 1) % wrap == 0:
                output_str += "<br>"

    return output_str


def mapping_data(
    input_path: Path = PROCESSED_DATA_DIR / "wrwc-processed-data-20260714.csv",
    output_path: Path = PROCESSED_DATA_DIR,
):
    """
    Creates data for mapping sites with summarized information.

    :param input_path: path to concentration file to use
    :param output_path: output directory
    :return: None
    """
    # Read in data
    df_data = pd.read_csv(input_path, parse_dates=['date'])
    df_site = pd.read_csv(RAW_DATA_DIR / "SiteInfo.csv")
    df_site.columns = [col.replace(" ", "_").lower() for col in df_site.columns]
    df_site.rename(columns={'ww_station': 'ww_id'}, inplace=True)

    # Aggregate parameters
    df_mapping = df_data.groupby(["ww_id"]).agg(
        {
            "parameter": lambda x: sorted(x.unique()),
            "date": lambda x: list(x.dt.year.unique()),
            "depth": lambda x: sorted(x.dropna().unique()),
        }
    )
    ...
    df_mapping = (
        df_mapping.merge(
            df_site.loc[:, ["ww_id", "wbid", "wb_type", "site_descr", "lat_dd", "lon_dd"]],
            left_index=True,
            right_on="ww_id",
            how="left",
        )
        .loc[
            :,
            [
                "ww_id",
                "wbid",
                "wb_type",
                "site_descr",
                "lat_dd",
                "lon_dd",
                "parameter",
                "date",
                "depth",
            ],
        ]
        .rename(columns={"parameter": "parameters", "date": "years", "depth": "depths"})
    )

    # Convert lists to strings for maping display
    df_mapping_out = df_mapping.assign(
        parameters=df_mapping["parameters"].apply(list_to_string),
        years=df_mapping["years"].apply(partial(list_to_string, wrap=8)),
        depths=df_mapping["depths"].apply(partial(list_to_string, wrap=10)),
    )

    date_str = datetime.now().strftime("%Y%m%d")
    df_mapping_out.to_csv(output_path / f"site_summary_{date_str}.csv", index=False)


if __name__ == "__main__":
    concentration_data()
    mapping_data()
