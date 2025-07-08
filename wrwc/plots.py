
import plotly.express as px


def plot_timeseries(df_mean, site, parameter, log=False):
    m = (df_mean['ww_id'] == site) & (df_mean['parameter'] == parameter)
    unit = df_mean.loc[m, 'year'].unique()
    years = df_mean.loc[m, 'year'].unique()
    year_range = range(min(years), max(years ) +1, 1)

    # Sample the color scale to get a color for each year
    continuous_scale = px.colors.sequential.Viridis
    year_colors = px.colors.sample_colorscale(continuous_scale, [ i /len(year_range) for i ,_ in enumerate(year_range)])

    # Create color map with index as key and color as value
    color_map_all = {year: color for year, color in zip(year_range, year_colors)}
    color_map = {year: color for year, color in color_map_all.items() if year in years}
    color_map_int = {i: color for i, color in enumerate(color_map.values())}

    plot_df = df_mean[m].sort_values(by='year-month')

    fig = px.line(plot_df, x="month", y="mean", color='year',
                  color_discrete_sequence=color_map_int, markers=True, log_y=log,
                  labels={'mean' :parameter, 'month' :'Month', 'year': 'Year'},
                  title=f'Site {site}'
                  )

    match parameter:
        case 'Phosphorus, Total':
            fig.add_hline(y=25,  line_dash="dash", line_color="red")
        case 'Enterococci':
            fig.add_hline(y=54,  line_dash="dash", line_color="red")
            fig.add_hline(y=33,  line_dash="dash", line_color="darkred")

    fig.show()


if __name__ == "__main__":
    ...
