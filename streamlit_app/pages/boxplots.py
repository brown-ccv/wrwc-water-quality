import pandas as pd
import streamlit as st
from streamlit_app.data_processing import (
    sites, site_name_lookup,
    load_concentration_data,
    get_ordered_sites
)
from streamlit_app.figures import plot_boxplot


@st.cache_data
def get_plot_data():
    wq_data = load_concentration_data(sites)

    # add a month column
    wq_data.reset_index(inplace=True)
    wq_data['month'] = wq_data['date'].dt.month

    return wq_data


def get_year_range_text(df):
    years = df['date'].dt.year.unique().astype(str)
    text = ', '.join(years)
    return text


@st.fragment
def boxplot_section(data: list[pd.DataFrame], names: list[str]):
    page = 'box'
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
    st.header('Boxplots')
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
        all_points = col2_2.checkbox('All data points', value=False)

    for i, (df, name) in enumerate(zip(data, names)):
        try:
            # Query site and parameter
            m = (df['ww_id'] == site_name_lookup.get(site_name)) & (df['parameter'] == parameter)
            plot_df = df[m]

            st.subheader(name)
            st.plotly_chart(
                plot_boxplot(
                    plot_df,
                    site_code=site_name_lookup.get(site_name),
                    site_name=site_name,
                    parameter=parameter,
                    log=log_scale,
                    all_points=all_points
                ),
                key=f'boxplot_{i}', use_container_width=True
            )

            st.caption(f"Years sampled: {get_year_range_text(plot_df)}")
        except IndexError as e:
            st.error(f"Error producing plot: {e}")
    if parameter == 'Fecal Coliform':
        st.info(
            "Note: Fecal Coliform methodology changed from CFU/100ml to MPN/100ml in 2011. "
            "The values are roughly equivalent but the analytical technique is different. "
            "This analysis presents unifies the units as MPN/100ml."
        )


# Page layout
data = get_plot_data()
boxplot_section([data], ['Site Concentrations by Month'])
