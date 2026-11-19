"""
Beta Bank Retention Desk: a worklist of customers likely to leave, a file per customer with the reasons and the
levers that would help, a churn map and the model's scorecard. Model in model/ (built by train.py), code in retention/.
"""

from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Retention Desk | Beta Bank | Ahmad Hassan", page_icon=":material/support_agent:",
                   layout="wide", initial_sidebar_state="expanded")

from desk.ui import inject_css  # noqa: E402
from nav import PAGES  # noqa: E402

st.logo(str(Path(__file__).parent / "assets" / "logo.svg"), size="large")
inject_css()
st.navigation(PAGES, position="sidebar").run()
