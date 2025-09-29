import streamlit as st
from collections import OrderedDict
from data_processing import (
    reverse_dict,
    load_map_data,
    load_concentration_data,
    process_monthly_count_data,
    process_temporal_bins
)
from figures import site_map, heatmap

# Read in site info and coordinates
sites = OrderedDict([('WW635', 'Whipple Field'),
                    ('WW437', 'Greystone Pond'),
                    ('WW226', 'Cricket Park'),
                    ('WW508', 'Manton Ave.'),
                    ('WW227', 'Donigian Park'),
                    ('WW308', 'Waterplace Park')])
site_name_lookup = reverse_dict(sites)


@st.cache_data
def get_map_data():
    gdf, df_cso = load_map_data(sites)
    return gdf, df_cso


@st.cache_data
def get_plot_data():
    wq_data = load_concentration_data(sites)
    count_data = process_monthly_count_data(wq_data, sites)
    df_cso_bin, df_4year_bin = process_temporal_bins(wq_data)

    return count_data, df_cso_bin, df_4year_bin


@st.fragment
def heatmap_section(counts):
    parameter_selection = sorted(counts.index.levels[0])
    heatmap_parameter = st.selectbox(
        label='Parameter',
        options=parameter_selection,
        key='heatmap_parameter'
    )
    st.plotly_chart(
        heatmap(
            counts.loc[heatmap_parameter],
            title=f'{heatmap_parameter} Counts by Site'
        )
    )


df_counts, df_cso_bins, df_4year_bins = get_plot_data()

# Layout
st.set_page_config(
    page_title="Riverine Sites",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Woonasquatucket River Lower Riverine Sites")

with st.expander("Site Map", expanded=True):
    fig = site_map(*get_map_data())
    st.plotly_chart(fig, use_container_width=True)

with st.expander("Sampling Counts", expanded=True):
    heatmap_section(df_counts)

