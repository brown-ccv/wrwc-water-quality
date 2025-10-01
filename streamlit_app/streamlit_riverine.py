import streamlit as st

st.set_page_config(
    page_title="Riverine Sites",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)
pg = st.navigation(["pages/explorer.py", "pages/timeseries.py"], expanded=True)
pg.run()


