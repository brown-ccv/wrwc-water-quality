import streamlit as st

st.set_page_config(
    page_title="Riverine Sites",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

explorer = st.Page("pages/explorer.py", title="Explorer", icon="🗺️")
timeseries = st.Page("pages/timeseries.py", title="Time Series", icon="📈")
boxplots = st.Page("pages/boxplots.py", title="Box Plots", icon="📦")

pg = st.navigation([explorer, boxplots, timeseries], expanded=True)
pg.run()


