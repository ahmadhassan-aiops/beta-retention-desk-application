"""Model scorecard: the F1 target, threshold trade-off, ROC, calibration, balancing and importance."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score, roc_curve

from desk import charts, data, fmt, ui


@st.cache_data
def _curve(y: np.ndarray, p: np.ndarray) -> pd.DataFrame:
    ts = np.round(np.arange(0.05, 0.91, 0.01), 2)
    return pd.DataFrame({"threshold": ts, "F1": [f1_score(y, p >= t) for t in ts],
                         "Recall": [recall_score(y, p >= t) for t in ts],
                         "Precision": [precision_score(y, p >= t, zero_division=0) for t in ts]})


def render() -> None:
    m = data.model()
    ref = data.reference()
    book = data.book()
    y, p = book["exited"].to_numpy(), book["proba"].to_numpy()
    s = ref["test"]
    ui.title("Scorecard", "Does the model meet the brief?",
             f"The brief: an <b>F1 score of at least 0.59</b> on unseen customers, with AUC-ROC reported. Everything "
             f"here is measured on the {len(book):,} held-out customers, scored once.")
    ui.target(s["F1"] >= 0.59, f"F1 {s['F1']:.3f}  ·  AUC-ROC {s['AUC-ROC']:.3f}",
              f"Target met: F1 above 0.59 at the threshold of {m.threshold:.2f}, chosen in cross-validation before the "
              "test set was opened.")
    order = np.argsort(-p)
    top20 = y[order[: len(y) // 5]].sum() / y.sum()
    ui.kpis([
        ("Recall", f"{s['Recall']:.1%}", "of leavers caught", "#3ec7b0"),
        ("Precision", f"{s['Precision']:.1%}", "of Act customers really left", "#6ea8fe"),
        ("PR-AUC", f"{s['PR-AUC']:.3f}", f"random scores {y.mean():.3f}", "#6ea8fe"),
        ("Top 20% of scores", f"{top20:.0%}", "of all leavers", "#ff7a59"),
    ])

    with ui.panel("01", "Move the act line", "F1, recall and precision on held-out customers"):
        th = st.slider("Act on customers at or above", 0.05, 0.90, m.threshold, 0.01, key="sc_t")
        a, b = st.columns([1.3, 1], gap="large")
        with a:
            charts.show(charts.threshold_curves(_curve(y, p), th, 0.59), "curves")
        with b:
            tn, fp, fn, tp = confusion_matrix(y, p >= th).ravel()
            charts.show(charts.confusion(tn, fp, fn, tp), "cm")
        ui.notes([f"At {th:.2f} the desk contacts <b>{tp + fp}</b> customers and catches <b>{tp} of {tp + fn}</b> leavers "
                  f"(F1 {f1_score(y, p >= th):.3f}). At the default 0.50 it would catch only "
                  f"{int(((p >= 0.5) & (y == 1)).sum())}."])

    a, b = st.columns(2, gap="large")
    with a:
        with ui.panel("02", "Ranking", "ROC curve"):
            fpr, tpr, _ = roc_curve(y, p)
            point = (fp / (fp + tn), tp / (tp + fn))
            charts.show(charts.roc(fpr, tpr, roc_auc_score(y, p), point), "roc")
    with b:
        with ui.panel("03", "Can the chances be trusted?", "out-of-fold calibration"):
            c = ref["calibration"]
            charts.show(charts.calibration(c["predicted"], c["observed"], c["customers"]), "cal")
            ui.notes(["The scores are calibrated: customers given about 40% left about 40% of the time, so the desk can use "
                      "them as real chances and multiply by balances to get deposits at risk."])

    with ui.panel("04", "How the imbalance was handled", "best out-of-fold F1 per approach, 5-fold cross-validation"):
        a, b = st.columns([1.3, 1], gap="large")
        with a:
            st.dataframe(pd.DataFrame(ref["balancing"]), hide_index=True, width="stretch",
                         column_config={"Best F1": st.column_config.NumberColumn(format="%.3f"),
                                        "AUC-ROC": st.column_config.NumberColumn(format="%.3f")})
        with b:
            ui.notes(["Only 20% of customers leave. SMOTE, undersampling and class weights were compared, each inside the "
                      "cross-validation folds, against simply <b>moving the threshold</b>.",
                      "Moving the threshold was as good as any resampling, and keeps the probabilities honest; resampled "
                      "models over-state how many customers will leave."])

    with ui.panel("05", "What the model relies on", "mean |SHAP| on held-out customers"):
        imp = ref["importance"]
        charts.show(charts.importance([fmt.SHORT[k] for k in imp], list(imp.values())), "imp")
    ui.footer()
