"""Method: data, how the model was built and chosen, limits, links."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from desk import data, ui
from desk.site import CODE_URL, NOTEBOOK_URL, PROJECT_URL


def render() -> None:
    m = data.model()
    ref = data.reference()
    ui.title("Method", "How the desk's model was built",
             "Data, model search, and what the model cannot do.")

    with ui.panel("01", "Data"):
        ui.notes([
            "<b>10,000 Beta Bank customers</b> in France, Germany and Spain; 2,037 (20.4%) left the bank.",
            "<b>Ten inputs:</b> country, gender, age, credit score, tenure, balance, products held, credit card, active "
            "member, estimated salary. Row number, customer ID and surname are not inputs (the surname only labels the "
            "worklist).",
            "<b>Tenure is missing for 909 customers</b>, at random (they churn at the average rate). The pipeline fills it "
            "with the training median.",
            "<b>Split:</b> 8,000 customers to train, 2,000 held out, stratified. Every choice used 5-fold cross-validation "
            "on the training customers; the held-out customers were scored once.",
        ])

    with ui.panel("02", "Model search"):
        a, b = st.columns([1.2, 1], gap="large")
    with a:
        st.dataframe(pd.DataFrame(ref["tuned"]), hide_index=True, width="stretch",
                     column_config={"AUC-ROC": st.column_config.NumberColumn(format="%.4f"),
                                    "Std": st.column_config.NumberColumn("Fold std", format="%.3f"),
                                    "Best F1": st.column_config.NumberColumn(format="%.3f")})
    with b:
        ui.notes([
            "Eight algorithms, with and without SMOTE, undersampling and class weights, all inside the folds.",
            "The best three were tuned (40 combinations each, AUC-ROC). They tie: the gaps are a tenth of the "
            "fold-to-fold variation.",
            f"XGBoost was deployed for its exact built-in explanations, which the customer file shows. The act line "
            f"<b>{m.threshold:.2f}</b> maximises F1 on out-of-fold predictions.",
        ])

    with ui.panel("03", "Limits"):
        ui.notes([
            "<b>Associations, not causes.</b> The levers on the customer file show how the score changes, not a proven "
            "effect of an action. Test retention offers against a control group.",
            "<b>One snapshot.</b> The data has no dates; churn drivers change with prices, competitors and the economy. "
            "Re-score monthly and retrain on new outcomes.",
            "<b>Fair treatment.</b> Gender and age are strong predictors. Use them to prioritise help, never to offer worse "
            "terms, and check the bank's rules before use.",
        ])

    with ui.panel("04", "Code and notebook"):
        st.markdown(f"- [Notebook]({NOTEBOOK_URL}): EDA, balancing comparison, tuning, threshold, SHAP\n"
                    f"- [Project folder]({PROJECT_URL}) in the portfolio repository\n"
                    f"- [App code]({CODE_URL}): Streamlit app, `retention/` inference package, `train.py`, tests")
    ui.footer()
