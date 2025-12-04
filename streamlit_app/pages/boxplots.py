import pandas as pd
import streamlit as st
from streamlit_app.data_processing import (
    sites, site_name_lookup,
    load_concentration_data,
    get_ordered_sites
)
from streamlit_app.figures import plot_boxplot, get_parameter_index


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
    st.header('Boxplots')
    col1, col2 = st.columns(2)

    # Site selection
    with col1:
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
        parameter = st.selectbox(
            label='Parameter',
            options=site_parameters,
            index=get_parameter_index(site_parameters, site_name)
        )
        # Update session state
        st.session_state.update({
            'selected_parameter': parameter,
            'selected_site': site_name
        })

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
