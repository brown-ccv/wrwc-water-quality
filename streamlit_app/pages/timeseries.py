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
    page = 'timeseries'
    df0 = data[0]
    sites_list = get_ordered_sites(df0)

    # Initialize state
    st.session_state.setdefault(
        f"{page}_site_store",
        sites_list[0]
    )

    initial_params = sorted(
        df0.loc[
            df0['ww_id'] == site_name_lookup[st.session_state[f'{page}_site_store']],
            'parameter'
        ].unique()
    )
    st.session_state.setdefault(
        f"{page}_param_store",
        initial_params[0]
    )

    # Display
    st.header('Timeseries')
    col1, col2 = st.columns(2)

    # Site selection
    with col1:
        site_name = st.selectbox(
            label='Site',
            options=sites_list,
            key=f"{page}_site",
            index=sites_list.index(st.session_state[f"{page}_site_store"])
        )
    st.session_state[f"{page}_site_store"] = site_name

    # Parameter selection
    site_parameters = sorted(
        df0.loc[
            df0['ww_id'] == site_name_lookup[st.session_state[f'{page}_site_store']],
            'parameter'
        ].unique()
    )

    # Only reset if invalid
    if st.session_state[f"{page}_param_store"] not in site_parameters:
        st.session_state[f"{page}_param_store"] = site_parameters[0]

    with col2:
        parameter = st.selectbox(
            label='Parameter',
            options=site_parameters,
            key=f"{page}_param_widget",
            index=site_parameters.index(
                st.session_state[f"{page}_param_store"]
            )
        )
        st.session_state[f"{page}_param_store"] = parameter

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


