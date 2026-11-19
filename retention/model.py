"""Load the trained pipeline, score, explain and simulate retention levers. No Streamlit here."""

from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb

from retention.schema import CATEGORICAL, FEATURES

MODEL_DIR = Path(__file__).resolve().parent.parent / "model"

# Things the bank can change, and what changing them means. (feature, new value, label, when it applies)
LEVERS = [
    ("IsActiveMember", 1, "Re-activate the customer", lambda c: c["IsActiveMember"] == 0),
    ("NumOfProducts", 2, "Move to exactly two products", lambda c: c["NumOfProducts"] != 2),
    ("HasCrCard", 1, "Add a credit card", lambda c: c["HasCrCard"] == 0),
]


class AttritionModel:
    """The saved scikit-learn pipeline (one-hot encoding, median imputation, tuned XGBoost) and its metadata."""

    def __init__(self, model_dir: Path = MODEL_DIR):
        self.pipeline = joblib.load(model_dir / "beta_bank_attrition_xgb.joblib")
        self.meta = json.loads((model_dir / "metadata.json").read_text(encoding="utf-8"))
        self.threshold: float = self.meta["threshold"]

    def predict_proba(self, rows: pd.DataFrame) -> np.ndarray:
        """Probability of leaving for rows that have the model's columns."""
        return self.pipeline.predict_proba(rows[FEATURES])[:, 1]

    def status(self, p: float) -> str:
        """Act (at or above the threshold), Monitor (from half of it) or Stable."""
        if p >= self.threshold:
            return "Act"
        return "Monitor" if p >= self.threshold / 2 else "Stable"

    @cached_property
    def _source(self) -> np.ndarray:
        names = self.pipeline.named_steps["prep"].get_feature_names_out()
        return np.array([next((c for c in CATEGORICAL if n.startswith(c + "_")), n) for n in names])

    def explain(self, rows: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
        """SHAP contribution of each original feature (log-odds) and the bias; bias + sum = log-odds of leaving."""
        encoded = self.pipeline.named_steps["prep"].transform(rows[FEATURES])
        contribs = self.pipeline.named_steps["model"].get_booster().predict(xgb.DMatrix(encoded), pred_contribs=True)
        grouped = pd.DataFrame(contribs[:, :-1], index=rows.index).T.groupby(self._source).sum().T
        return grouped[FEATURES], contribs[:, -1]

    def levers(self, row: pd.DataFrame) -> list[dict]:
        """For one customer: each applicable lever, the probability after pulling it, and the change."""
        base = float(self.predict_proba(row)[0])
        customer = row.iloc[0]
        out = []
        for feature, value, label, applies in LEVERS:
            if not applies(customer):
                continue
            changed = row.copy()
            changed[feature] = value
            p = float(self.predict_proba(changed)[0])
            out.append({"feature": feature, "label": label, "before": base, "after": p, "change": p - base})
        if len(out) > 1:  # all applicable levers together
            changed = row.copy()
            for o in out:
                changed[o["feature"]] = next(v for f, v, *_ in LEVERS if f == o["feature"])
            p = float(self.predict_proba(changed)[0])
            out.append({"feature": "all", "label": "All of the above", "before": base, "after": p, "change": p - base})
        return sorted(out, key=lambda o: o["change"])


def to_prob(logit: float) -> float:
    return float(1 / (1 + np.exp(-logit)))
