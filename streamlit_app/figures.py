import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def site_map(gdf, df_cso):

    fig = px.scatter_map(gdf,
                         lat=gdf.geometry.y, lon=gdf.geometry.x,
                         hover_name="site_descr",
                         hover_data=["ww_id", "parameters", "years", "depths"],
                         color_discrete_sequence=['purple'],
                         size=[1 for s in range(len(gdf))],
                         size_max=8,
                         zoom=11.5, width=1000, height=900,
                         )

    # Add df_cso points using go.Scattermap (not deprecated)
    fig.add_trace(go.Scattermap(
        lat=df_cso.geometry.y.tolist(),
        lon=df_cso.geometry.x.tolist(),
        mode='markers',
        marker=dict(
            size=6,
            color='red',
            opacity=0.5
        ),
        name='CSO',
        hoverinfo='text',
        text=[f"CSO ID: {i}" for i in df_cso['OF_']]
    ))

    # Make sure the legend shows for all traces
    fig.update_traces(showlegend=True)
    fig.data[0].name = "Sample Locations"

    return fig


def heatmap(df, title):
    fig = go.Figure(data=go.Heatmap(
        z=df.values,
        x=df.columns,
        y=df.index,
    ))

    fig.update_layout(
        title=dict(text=title),
        xaxis_nticks=32)
    fig.update_xaxes(tickangle=90)
    fig.update_yaxes(autorange="reversed")

    return fig


def get_unit(df, column='unit'):
    unit = df[column].unique()
    if len(unit) > 1:
        unit = ", ".join(unit)
    else:
        unit = unit[0]
    return unit


def plot_timeseries(df_mean, site_code, site_name, parameter, log=False, minmax=False):
    m = (df_mean['ww_id'] == site_code) & (df_mean['parameter'] == parameter)

    color_by = 'year_range'
    if 'pre_2015' in df_mean.columns:
        color_by = 'pre_2015'

    bins = df_mean.loc[m, color_by].unique()
    # Sample the color scale to get a color for each year
    continuous_scale = px.colors.sequential.Viridis
    bin_colors = px.colors.sample_colorscale(continuous_scale,
                                             [i / len(bins) for i, _ in enumerate(bins)])

    # Create color map with index as key and color as value
    color_map = {bin_val: color for bin_val, color in zip(bins, bin_colors)}
    color_map_int = {i: color for i, color in enumerate(color_map.values())}

    plot_df = df_mean[m]  # .sort_values(by='year-month')
    unit = get_unit(plot_df)

    fig = px.line(plot_df, x="month", y="mean", color=color_by,
                  markers=True, log_y=log, color_discrete_sequence=color_map_int,
                  labels={'mean': f"{parameter} ({unit})", 'month': 'Month'},
                  title=f'Site: {site_name}, {site_code}'
                  )
    fig.update_traces(line=dict(width=2.5))

    if minmax:
        # Add min and max lines for each year bin
        for bin_val in bins:
            bin_data = plot_df[plot_df[color_by] == bin_val]
            bin_color = color_map[bin_val]

            # Add min line (dashed)
            fig.add_scatter(
                x=bin_data["month"],
                y=bin_data["min"],  # assuming your min column is named 'min'
                mode='lines',
                line=dict(color=bin_color, dash='dot'),
                opacity=.5,
                name=f'{bin_val} Min',
                showlegend=False
            )

            # Add max line (dashed)
            fig.add_scatter(
                x=bin_data["month"],
                y=bin_data["max"],  # assuming your max column is named 'max'
                mode='lines',
                line=dict(color=bin_color, dash='dot'),
                opacity=.5,
                name=f'{bin_val} Max',
                showlegend=False
            )

    match parameter:
        case 'Phosphorus, Total':
            fig.add_hline(y=25, line_dash="dash", line_color="red")
        case 'Enterococci':
            fig.add_hline(y=54, line_dash="dash", line_color="red")
            fig.add_hline(y=33, line_dash="dash", line_color="darkred")
        case 'pH':
            fig.add_hline(y=6.5, line_dash="dash", line_color="red")
            fig.add_hline(y=9.0, line_dash="dash", line_color="red")
        case 'Dissolved Oxygen':
            fig.add_hline(y=5.0, line_dash="dash", line_color="red")

    return fig


def plot_boxplot(df, site_code, site_name, parameter, log=False, all_points=False):
    unit = get_unit(df)
    point_display = ('all' if all_points else 'outliers')

    fig = px.box(df, x='month', y='concentration',
                 log_y=log, points=point_display,
                 labels={'concentration': f"{parameter} ({unit})", 'month': 'Month'},
                 hover_data={'date': '|%Y-%m-%d', 'concentration': True, 'month': False},
                 title=f'Site: {site_name}, {site_code}')
    return fig


def get_parameter_index(site_parameters: list[str], current_site: str) -> int:
    """
    Determine the default parameter index, preserving selection across site changes when possible.
    """
    # Check if site has changed
    previous_site = st.session_state.get('selected_site')
    previous_parameter = st.session_state.get('selected_parameter')

    site_changed = previous_site != current_site
    parameter_available = previous_parameter in site_parameters

    if site_changed and parameter_available:
        return site_parameters.index(previous_parameter)

    return 0  # Default to first parameter
