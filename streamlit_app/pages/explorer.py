import streamlit as st
from streamlit_app.data_processing import (
    sites, site_name_lookup,
    load_map_data,
    load_concentration_data,
    process_monthly_count_data,
)
from streamlit_app.figures import site_map, heatmap


@st.cache_data
def get_map_data():
    gdf, df_cso = load_map_data(sites)
    return gdf, df_cso


@st.cache_data
def get_plot_data():
    wq_data = load_concentration_data(sites)
    count_data = process_monthly_count_data(wq_data, sites)
    return count_data


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


df_counts = get_plot_data()

st.title("Woonasquatucket River Lower Riverine Sites")

with st.expander("Site Map", expanded=True):
    fig = site_map(*get_map_data())
    st.plotly_chart(fig, use_container_width=True)

with st.expander("Sampling Counts", expanded=True):
    heatmap_section(df_counts)

    # Padding at the bottom of the page to prevent browser auto scroll anchoring
    # issues in firefox and safari.
st.markdown("<div style='height:600px;'></div>", unsafe_allow_html=True)
