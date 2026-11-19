"""Worklist: today's queue of customers to call, ranked by deposits or chance at risk."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from desk import charts, data, fmt, ui
from desk import theme as t
from retention.schema import FEATURES, validate_rows

QUEUE = 9


@st.cache_data
def _reasons(frame: pd.DataFrame) -> list[list[str]]:
    """The two features that raise each customer's score most."""
    contrib, _ = data.model().explain(frame[FEATURES])
    out = []
    for i, row in contrib.iterrows():
        top = row[row > 0.15].sort_values(ascending=False).index[:2]
        out.append([fmt.reason(f, frame.loc[i, f]) for f in top])
    return out


def _open(cid: int) -> None:
    st.session_state["file_id"] = int(cid)
    st.session_state["file_mode"] = "From the book"


def _upload() -> pd.DataFrame | None:
    up = st.sidebar.file_uploader("Your customer file (CSV)", type="csv",
                                  help="Columns: " + ", ".join(FEATURES) + ". Optional: CustomerId, Surname.")
    if up is None:
        return None
    raw = pd.read_csv(up)
    clean, errors = validate_rows(raw)
    if errors:
        st.sidebar.warning("\n\n".join(errors[:5]), icon=":material/rule:")
    if clean.empty:
        return None
    clean = clean.copy()
    clean.insert(0, "Surname", raw.loc[clean.index, "Surname"] if "Surname" in raw else "Customer")
    clean.insert(0, "CustomerId", raw.loc[clean.index, "CustomerId"] if "CustomerId" in raw else range(1, len(clean) + 1))
    clean["proba"] = data.model().predict_proba(clean)
    clean["at_risk"] = clean["proba"] * clean["Balance"]
    return clean.reset_index(drop=True)


def render() -> None:
    m = data.model()
    st.sidebar.markdown("**Book**")
    source = st.sidebar.radio("Customers", ["Held-out book (2,000)", "Upload a file"], label_visibility="collapsed",
                              key="wl_source")
    book = _upload() if source == "Upload a file" else data.book()
    if book is None:
        ui.title("Worklist", "Load a customer file", "Upload a CSV in the sidebar to score your own customers.")
        ui.footer()
        return
    known = "exited" in book

    st.sidebar.markdown("**Filter**")
    countries = st.sidebar.multiselect("Country", ["France", "Germany", "Spain"], default=["France", "Germany", "Spain"])
    ages = st.sidebar.slider("Age", 18, 92, (18, 92))
    sort = st.sidebar.radio("Rank by", ["Deposits at risk", "Chance of leaving"], key="wl_sort")

    book = book.assign(status=[m.status(p) for p in book["proba"]], reasons=_reasons(book))
    view = book[book["Geography"].isin(countries) & book["Age"].between(*ages)]
    view = view.sort_values("at_risk" if sort == "Deposits at risk" else "proba", ascending=False)
    act = view[view["status"] == "Act"]

    ui.title("Worklist", "Who should we call today?",
             f"Every customer in the book is scored for their chance of leaving. <b>{len(act):,} are above the act "
             f"line ({m.threshold:.0%})</b>; ranked by {sort.lower()}, the top of the queue is where a call protects the "
             f"most. {'These are 2,000 customers the model never saw, so you can check its calls against what happened.' if known else ''}")
    items = [
        ("Customers", f"{len(view):,}", f"{len(view) / len(book):.0%} of the book after filters", t.BLUE),
        ("Act now", f"{len(act):,}", f"chance ≥ {m.threshold:.0%}", t.CORAL),
        ("Expected leavers", f"{view['proba'].sum():,.0f}", f"{view['proba'].mean():.1%} average chance", t.AMBER),
        ("Deposits at risk", ui.money(view["at_risk"].sum()), f"of {ui.money(view['Balance'].sum())} held", t.CORAL),
    ]
    if known:
        caught = int(act["exited"].sum())
        items.append(("Leavers caught", f"{caught}",
                      f"of {int(view['exited'].sum())} who left; {act['exited'].mean():.0%} of Act did leave"
                      if len(act) else "", t.TEAL))
    ui.kpis(items)

    with ui.panel("01", "Today's queue", f"top {QUEUE} by {sort.lower()}"):
        cols = st.columns(3)
        for i, (_, r) in enumerate(view.head(QUEUE).iterrows()):
            with cols[i % 3].container(border=True):
                ui.customer_card(str(r["Surname"]), int(r["CustomerId"]), r["Geography"], r["status"], float(r["proba"]),
                                 float(r["Balance"]), r["reasons"])
                if st.button("Open file", key=f"open_{r['CustomerId']}_{i}", icon=":material/folder_open:",
                             on_click=_open, args=(r["CustomerId"],), width="stretch", disabled=not known):
                    from nav import FILE
                    st.switch_page(FILE)

    with ui.panel("02", "Where the deposits at risk sit", "size = chance × balance · colour = average chance"):
        charts.show(charts.treemap(view), "treemap")
        by_c = view.groupby("Geography")["at_risk"].sum().sort_values(ascending=False)
        if len(by_c):
            ui.caveat(f"<b>{by_c.index[0]}</b> holds {by_c.iloc[0] / by_c.sum():.0%} of the deposits at risk in this view. "
                      "Customers with a zero balance put no deposits at risk, so they appear only when ranking by chance.")

    with ui.panel("03", "Full list", "select a row to open the customer's file"):
        table = view.assign(Name=view["Surname"], Chance=view["proba"] * 100, Why=view["reasons"].map(", ".join))
        cols_show = ["CustomerId", "Name", "status", "Chance", "at_risk", "Balance", "Geography", "Age", "NumOfProducts",
                     "IsActiveMember", "Why"] + (["exited"] if known else [])
        event = st.dataframe(
            table[cols_show], hide_index=True, height=420, width="stretch", on_select="rerun",
            selection_mode="single-row", key="wl_table",
            column_config={
                "CustomerId": st.column_config.NumberColumn("ID", format="%d"),
                "status": "Status",
                "Chance": st.column_config.ProgressColumn("Chance of leaving", min_value=0, max_value=100, format="%.0f%%"),
                "at_risk": st.column_config.NumberColumn("At risk", format="compact"),
                "Balance": st.column_config.NumberColumn(format="compact"),
                "Geography": "Country", "NumOfProducts": "Products",
                "IsActiveMember": st.column_config.CheckboxColumn("Active"),
                "Why": "Main reasons", "exited": st.column_config.CheckboxColumn("Actually left"),
            },
        )
        rows = event.selection.rows if event else []
        if rows and known:
            _open(table.iloc[rows[0]]["CustomerId"])
            from nav import FILE
            st.switch_page(FILE)
        st.download_button("Download the scored list (CSV)", view.drop(columns=["reasons"]).to_csv(index=False).encode(),
                           "retention_worklist.csv", "text/csv", icon=":material/download:")
    ui.footer()
