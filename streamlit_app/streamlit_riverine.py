import streamlit as st
from collections import OrderedDict
from streamlit_app.data_processing import (
    sites, site_name_lookup,
    load_map_data,
    load_concentration_data,
    process_monthly_count_data,
    process_temporal_bins
)
from streamlit_app.figures import site_map, heatmap, plot_timeseries


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


@st.fragment
def timeseries_section(data, section_key=0):
    # st.dataframe(data)
    col1, col2 = st.columns(2)

    # Site selection
    with col1:
        site_names = [sites[s] for s in data['ww_id'].unique()]
        site_name = st.selectbox(
            label='Site',
            options=site_names,
            key=f'site_name_{section_key}'
        )

    # Parameter selection
    with col2:
        site_parameters = sorted(
            data.
            loc[data['ww_id'] == site_name_lookup[site_name], 'parameter']
            .unique()
        )
        parameter = st.selectbox(
            label='Parameter',
            options=site_parameters,
            key=f'site_parameter_{section_key}'
        )

        # Checkbox selectors
        col2_1, col2_2 = st.columns(2)
        log_scale = col2_1.checkbox('log scale', value=False, key=f'log_scale_{section_key}')
        min_max = col2_2.checkbox('Min-Max lines', value=False, key=f'min_max_{section_key}')

    st.plotly_chart(
        plot_timeseries(
            data,
            site_code=site_name_lookup.get(site_name),
            site_name=site_name,
            parameter=parameter,
            log=log_scale,
            minmax=min_max
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

with st.expander("Timeseries 4-year bins", expanded=True):
    timeseries_section(df_4year_bins)

with st.expander("Timeseries CSO update", expanded=True):
    timeseries_section(df_cso_bins, section_key=1)

