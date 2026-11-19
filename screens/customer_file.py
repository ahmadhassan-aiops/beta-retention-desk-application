"""Customer file: one customer's profile, chance of leaving, why (waterfall), and which levers would help."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from desk import charts, data, fmt, ui
from retention.model import to_prob
from retention.schema import COUNTRIES, FEATURES, GENDERS, LABELS, NUMERICAL, Customer

NEW = {"Geography": "Germany", "Gender": "Female", "CreditScore": 650, "Age": 52, "Tenure": 5.0, "Balance": 120000.0,
       "NumOfProducts": 1, "HasCrCard": 1, "IsActiveMember": 0, "EstimatedSalary": 100000.0}


def _from_book() -> tuple[pd.DataFrame, pd.Series | None]:
    book = data.book().sort_values("proba", ascending=False).reset_index(drop=True)
    ids = book["CustomerId"].tolist()
    current = st.session_state.get("file_id", ids[0])
    choice = st.selectbox(
        "Customer", ids, index=ids.index(current) if current in ids else 0, key="file_pick",
        format_func=lambda cid: (lambda r: f"{r['Surname']} · #{cid} · {r['Geography']} · {ui.pct(r['proba']).replace('&gt;', '>').replace('&lt;', '<')}")(
            book.loc[book["CustomerId"] == cid].iloc[0]),
    )
    st.session_state["file_id"] = choice
    row = book.loc[book["CustomerId"] == choice].iloc[0]
    frame = pd.DataFrame([row[FEATURES].to_dict()]).astype({c: float for c in NUMERICAL})
    return frame, row


def _form() -> pd.DataFrame | None:
    with st.container(border=True):
        a, b, c, d = st.columns(4)
        v = dict(
            Geography=a.selectbox("Country", COUNTRIES, index=COUNTRIES.index(NEW["Geography"])),
            Gender=b.selectbox("Gender", GENDERS),
            Age=c.number_input("Age", 18, 100, NEW["Age"]),
            CreditScore=d.number_input("Credit score", 300, 900, NEW["CreditScore"]),
        )
        a, b, c, d = st.columns(4)
        v["Balance"] = a.number_input("Balance", 0.0, 1_000_000.0, NEW["Balance"], step=5000.0, format="%.0f")
        v["EstimatedSalary"] = b.number_input("Estimated salary", 0.0, 1_000_000.0, NEW["EstimatedSalary"], step=5000.0,
                                              format="%.0f")
        v["Tenure"] = c.number_input("Tenure (years)", 0, 10, int(NEW["Tenure"]))
        v["NumOfProducts"] = d.number_input("Products held", 1, 4, NEW["NumOfProducts"])
        a, b, _ = st.columns([1, 1, 2])
        v["IsActiveMember"] = int(a.toggle("Active member", bool(NEW["IsActiveMember"])))
        v["HasCrCard"] = int(b.toggle("Has a credit card", bool(NEW["HasCrCard"])))
    try:
        return Customer(**v).to_frame()
    except ValidationError as exc:
        st.error(exc.errors()[0]["msg"], icon=":material/error:")
        return None


def _play(levers: list[dict], status: str) -> str:
    best = next((lv for lv in levers if lv["feature"] != "all" and lv["change"] <= -0.03), None)
    if status == "Stable":
        return "No retention action needed. Keep the customer in normal service and re-score next month."
    if best is None:
        return ("None of the bank's levers moves this score much: what drives it (such as age or country) cannot be "
                "changed. A personal call to understand their plans is the best use of time.")
    text = {
        "IsActiveMember": "Re-engage them: a call from their adviser, a review of how they use the account, and a reason "
                          "to bank actively again (fee waiver, better rate for regular use).",
        "NumOfProducts": "Review their products. Customers with exactly two products are the most loyal; "
                         "consolidate an unwanted third or fourth product, or offer a well-matched second one.",
        "HasCrCard": "Offer a credit card that fits their spending.",
    }[best["feature"]]
    return f"{text} The model expects this to cut their chance of leaving from {ui.pct(best['before'])} to {ui.pct(best['after'])}."


def render() -> None:
    m = data.model()
    ui.title("Customer file", "One customer, in full",
             "Open a customer from the worklist or pick one here, or enter a new customer. The file shows their chance "
             "of leaving, <b>why</b>, and <b>which of the bank's levers would bring it down</b>.")
    mode = st.segmented_control("Source", ["From the book", "Enter a customer"], default="From the book",
                                required=True, key="file_mode", label_visibility="collapsed")
    if mode == "From the book":
        row, record = _from_book()
    else:
        row, record = _form(), None
        if row is None:
            return
    p = float(m.predict_proba(row)[0])
    status = m.status(p)
    contrib, bias = m.explain(row)
    contrib = contrib.iloc[0]
    customer = row.iloc[0]

    left, right = st.columns([1, 1.7], gap="large")
    with left:
        with st.container(border=True):
            name = f"{record['Surname']} · #{int(record['CustomerId'])}" if record is not None else "New customer"
            st.html(f'<p class="c-name">{name}</p><div style="margin:.4rem 0">{ui.pill(status)}</div>')
            ui.led_meter(p, m.threshold, status, "chance of leaving")
            ui.sheet([(LABELS[f], fmt.value(f, customer[f])) for f in FEATURES])
            if record is not None:
                left_bank = bool(record["exited"])
                ui.caveat(f"<b>What happened:</b> this held-out customer {'left the bank' if left_bank else 'stayed'}. "
                          "The model never saw them in training.")
    with right:
        ui.section("01", "Why this score", "largest effects first, in percentage points")
        top = contrib.reindex(contrib.abs().sort_values(ascending=False).index)
        shown = top[:6]
        rest = float(top[6:].sum())
        steps = [(fmt.SHORT[f], fmt.value(f, customer[f]), float(c)) for f, c in shown.items()]
        if abs(rest) > 1e-6:
            steps.append(("Other 4 factors", "combined", rest))
        charts.show(charts.waterfall(to_prob(float(bias[0])), steps, p), "waterfall")
        ui.caveat("Each bar is how much one fact moves the chance, starting from the average customer (SHAP values from "
                  "the model, applied largest first). Coral raises the chance of leaving, teal lowers it.")

    ui.section("02", "Retention levers", "what the model expects if the bank changes one thing")
    levers = m.levers(row)
    if levers:
        with st.container(border=True):
            ui.levers(levers)
    else:
        ui.caveat("This customer is already active, has two products and a credit card: no lever left to pull.")
    ui.play(_play(levers, status))
    ui.caveat("<b>Read with care:</b> the model learned from what customers like this did, not from experiments. A lever "
              "shows the score a customer with that profile would get; it is a guide to where to start, not a promise.")
    ui.footer()
