import pandas as pd
import streamlit as st
from streamlit_app.data_processing import (
    sites, site_name_lookup,
    load_concentration_data,
    process_temporal_bins, get_ordered_sites
)
from streamlit_app.figures import plot_timeseries


@st.cache_data
def get_plot_data():
    wq_data = load_concentration_data(sites)
    df_4year_bin, df_cso_bin = process_temporal_bins(wq_data)

    return df_4year_bin, df_cso_bin


@st.fragment
def timeseries_section(data: list[pd.DataFrame], names: list[str]):
    st.header('Timeseries')
    col1, col2 = st.columns(2)

    # Site selection
    with col1:
        site_names = [sites[s] for s in data[0]['ww_id'].unique()]
        site_name = st.selectbox(
            label='Site',
            options=get_ordered_sites(data[0]),
        )

    # Parameter selection
    with col2:
        site_parameters = sorted(
            data[0]
            .loc[data[0]['ww_id'] == site_name_lookup[site_name], 'parameter']
            .unique()
        )

        # Determine the default parameter index
        default_index = 0
        if 'selected_parameter' in st.session_state:
            # Check if the previously selected parameter is available for this site
            if st.session_state.selected_parameter in site_parameters:
                default_index = site_parameters.index(st.session_state.selected_parameter)

        parameter = st.selectbox(
            label='Parameter',
            options=site_parameters,
            index=default_index,
        )
        st.session_state.selected_parameter = parameter

        # Checkbox selectors
        col2_1, col2_2 = st.columns(2)
        log_scale = col2_1.checkbox('log scale', value=False)
        min_max = col2_2.checkbox('Min-Max lines', value=False)

    for i, (df, name) in enumerate(zip(data, names)):
        try:
            st.subheader(name)
            st.plotly_chart(
                plot_timeseries(
                    df,
                    site_code=site_name_lookup.get(site_name),
                    site_name=site_name,
                    parameter=parameter,
                    log=log_scale,
                    minmax=min_max
                ),
                key=f'timeseries_{i}', use_container_width=True
            )
        except IndexError as e:
            st.info("Pre and post CSO improvements is only available for sites: "
                    "Greystone Pond, Donigian Park, and Waterplace Park.")
    if parameter == 'Fecal Coliform':
        st.info(
            "Note: Fecal Coliform methodology changed from CFU/100ml to MPN/100ml in 2011. "
            "The values are roughly equivalent but the analytical technique is different. "
            "This analysis presents unifies the units as MPN/100ml."
        )


# Page layout
df_4year_bins, df_cso_bins = get_plot_data()
timeseries_section(
    data=[df_4year_bins, df_cso_bins],
    names=['~4 year bins', 'Pre and Post 2015 CSO improvements']
)

# Padding at the bottom of the page to prevent browser auto scroll anchoring
# issues in firefox and safari.
st.markdown("<div style='height:1000px;'></div>", unsafe_allow_html=True)


