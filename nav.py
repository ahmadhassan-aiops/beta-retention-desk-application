"""Page registry (sidebar navigation), shared by app.py and screens that link to other screens."""

import streamlit as st

from screens import churn_map, customer_file, method, scorecard, worklist

WORKLIST = st.Page(worklist.render, title="Worklist", icon=":material/format_list_numbered:", url_path="worklist",
                   default=True)
FILE = st.Page(customer_file.render, title="Customer file", icon=":material/folder_shared:", url_path="customer")
MAP = st.Page(churn_map.render, title="Churn map", icon=":material/insights:", url_path="churn-map")
SCORECARD = st.Page(scorecard.render, title="Scorecard", icon=":material/rule:", url_path="scorecard")
METHOD = st.Page(method.render, title="Method", icon=":material/menu_book:", url_path="method")

PAGES = {"Desk": [WORKLIST, FILE], "Analysis": [MAP, SCORECARD, METHOD]}
