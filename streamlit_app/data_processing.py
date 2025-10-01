import pandas as pd
import numpy as np
import geopandas as gpd
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
    df_site = (pd.read_csv(PROCESSED_DATA_DIR / 'site_summary_20250424.csv')
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


def load_concentration_data(sites: dict[str, str]):
    wq_data = (
        pd.read_csv(PROCESSED_DATA_DIR / "wrwc-processed-data-20250501.csv", parse_dates=['date'])
        .query(f"ww_id in {list(sites.keys())}")
        .set_index('date')
    )

    # Standardize unit for Fecal Coliforms
    wq_data.loc[wq_data['parameter'] == 'Fecal Coliform', 'unit'] = 'MPN/100ml'

    return wq_data


def process_monthly_count_data(data: pd.DataFrame, sites: dict[str, str]):
    counts = (
        data
        .groupby(['parameter', 'ww_id'])
        .resample("MS")
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
    df_mean_cso = (
        df_temporal
        .groupby(by=['ww_id', 'parameter', 'unit', 'pre_2015', 'month'], observed=True)[
            'concentration']
        .agg(['mean', 'min', 'max', 'count'])
        .query("ww_id in ['WW227', 'WW308', 'WW437']")
        .reset_index()
    )

    df_mean_year_range = (
        df_temporal
        .groupby(by=['ww_id', 'parameter', 'unit', 'year_range', 'month'], observed=True)[
            'concentration']
        .agg(['mean', 'min', 'max', 'count'])
        .query("ww_id not in ['WW508']")
        .reset_index()
    )

    return df_mean_cso, df_mean_year_range
