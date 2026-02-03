import pandas as pd
import numpy as np
import geopandas as gpd
from gsw import O2sol
from collections import OrderedDict
from wrwc.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, EXTERNAL_DATA_DIR


def reverse_dict(dictionary: OrderedDict):
    return OrderedDict([(name, code) for code, name in dictionary.items()])


# Read in site info and coordinates
sites = OrderedDict([('WW635', 'Whipple Field'),
                    ('WW437', 'Greystone Pond'),
                    ('WW226', 'Cricket Park'),
                    ('WW508', 'Manton Ave.'),
                    ('WW227', 'Donigian Park'),
                    ('WW308', 'Waterplace Park')])
site_name_lookup = reverse_dict(sites)


def load_map_data(sites: dict[str, str]):
    df_site = (pd.read_csv(PROCESSED_DATA_DIR / 'site_summary_20250708.csv')
               .query(f"ww_id in {list(sites.keys())}")
               .rename(columns={'lon_dd': 'lon', 'lat_dd': 'lat'})
               )
    # convert to geo-df
    gdf = gpd.GeoDataFrame(
        df_site,
        geometry=gpd.points_from_xy(df_site['lon'], df_site['lat']),
        crs='epsg:4326'
    )

    # Read CSO points
    df_cso = gpd.read_file(
        EXTERNAL_DATA_DIR / 'UTILITY_NBC_Sewer_Overflows_spf_-4273409046426376393.gpkg')
    df_cso = df_cso.to_crs(gdf.crs)

    return gdf, df_cso


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
            .apply(_interpolate_temperature)
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
    df_do = (
        df
        .loc[m, ['ww_id', 'parameter', 'concentration']]
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
    df_do_sat = _dissolved_oxygen_saturation(df_interp)

    # Append calculated values
    df_out = pd.concat([df, df_do_sat], axis=0, ignore_index=False)

    return df_out


def load_concentration_data(sites: dict[str, str]):
    wq_data = (
        pd.read_csv(PROCESSED_DATA_DIR / "wrwc-processed-data-20250501.csv", parse_dates=['date'])
        .query(f"ww_id in {list(sites.keys())}")
        .set_index('date')
    )

    # Standardize unit for Fecal Coliforms
    wq_data.loc[wq_data['parameter'] == 'Fecal Coliform', 'unit'] = 'MPN/100ml'

    # Calculate dissolved oxygen concentration
    wq_data_with_do = calculate_dissolved_oxygen_saturation(wq_data)

    return wq_data_with_do


def process_monthly_count_data(data: pd.DataFrame, sites: dict[str, str]):
    counts = (
        data
        .groupby(['parameter', 'ww_id'])
        .resample("MS", include_groups=False)
        .size()
        .unstack(fill_value=0)
        .reindex(sites.keys(), level=1)
    )
    return counts


def process_temporal_bins(data: pd.DataFrame):
    bins = [1990, 2003, 2007, 2011, 2015, 2019, 2022]  # End points of intervals
    labels = ['<2003', '2003-2006', '2007-2010', '2011-2014', '2015-2018', '2019-2021']
    data = data.reset_index()
    df_temporal = (
        data
        .assign(
            pre_2015=lambda x: ['pre' if year < 2015 else 'post' for year in x['date'].dt.year],
            year_range=pd.cut(data['date'].dt.year, bins=bins, labels=labels,
                              include_lowest=True, right=False),
            year=data['date'].dt.year,
            month=data['date'].dt.month
        )
    )

    # Aggregate measures across year ranges by month
    df_mean_year_range = (
        df_temporal
        .groupby(by=['ww_id', 'parameter', 'unit', 'year_range', 'month'], observed=True)[
            'concentration']
        .agg(['mean', 'min', 'max', 'count'])
        .query("ww_id not in ['WW508']")
        .reset_index()
    )

    df_mean_cso = (
        df_temporal
        .groupby(by=['ww_id', 'parameter', 'unit', 'pre_2015', 'month'], observed=True)[
            'concentration']
        .agg(['mean', 'min', 'max', 'count'])
        .query("ww_id in ['WW227', 'WW308', 'WW437']")
        .reset_index()
        .sort_values(
            by=['ww_id', 'parameter', 'unit', 'pre_2015', 'month'],
            ascending=[True, True, True, False, True]
        )
    )

    return df_mean_year_range, df_mean_cso


def get_ordered_sites(df):
    """Defines upstream to downstream site order."""
    site_order = ["Whipple Field", "Greystone Pond", "Cricket Park",
                  "Manton Ave.", "Donigian Park", "Waterplace Park"]
    sort_key = {site: i for i, site in enumerate(site_order)}

    sites_in_data = [sites[s] for s in df['ww_id'].unique()]
    ordered_sites = sorted(sites_in_data, key=lambda site: sort_key.get(site, float('inf')))

    return ordered_sites
