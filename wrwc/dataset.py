from datetime import datetime
import pandas as pd
import typer
from pathlib import Path
from loguru import logger


from wrwc.config import PROCESSED_DATA_DIR, RAW_DATA_DIR

app = typer.Typer()


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = RAW_DATA_DIR / 'WoonasquatucketData.csv',
    output_path: Path = PROCESSED_DATA_DIR,
    # ----------------------------------------------
):
    logger.info("Processing dataset...")

    site_info_path = RAW_DATA_DIR / 'SiteInfo.csv'

    # Read in data
    df_data_raw = pd.read_csv(input_path)
    df_data = df_data_raw.copy()
    df_site = pd.read_csv(site_info_path)

    # Standardize column names
    df_data.columns = [col.replace(" ", "_").lower() for col in df_data.columns]

    # Create dictionary of parameter codes to parameter name for relabeling with concise names
    param_code_to_name = {s.split('-')[-1].strip(): s.split('-')[0].strip() for s in
                          df_data.parameter.unique()}
    shortened_names = {'00915': 'Calcium',
                       '32209': 'Chlorophyll a',
                       '82903': 'Depth',
                       '00631': 'Nitrate + Nitrite',
                       '00930': 'Sodium',
                       '00600': 'Nitrogen, Total',
                       '00608': 'Nitrogen, Ammonia',
                       }
    param_code_to_name.update(shortened_names)

    # Process Site info
    df_site.columns = [col.replace(" ", "_").lower() for col in df_site.columns]
    df_site.rename(columns={'ww_station': 'ww_id'}, inplace=True)

    # Process dataframe
    df_data = (
        df_data
        # Create datetime, parameter code, and parameter name columns
        .assign(date=pd.to_datetime(df_data['date_of_sample']),
                param_code=[s.split('-')[-1].strip() for s in df_data['parameter']],
                unit=df_data['unit'].replace('mg/L', 'mg/l'))
        .assign(parameter=lambda x: [param_code_to_name[s] for s in x['param_code']])
        # Drop no data or redundant columns
        .drop(columns=['sediment_particle_size', 'particle_size_unit', 'fish_sample_type',
                       'fish_taxa', 'date_of_sample'])
        .merge(df_site.loc[:, ['ww_id', 'wbid', 'wb_type', 'site_descr', 'lat_dd', 'lon_dd']],
               on='ww_id', how='left')
    )
    logger.success("Processing dataset complete.")

    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"wrwc-processed-data-{date_str}.csv"
    df_data.to_csv(output_path / filename, index=False)
    # -----------------------------------------


if __name__ == "__main__":
    app()
