"""
Reproduce model/ and data/ from the raw dataset (the research is in the notebook; this replays the final choice):

    python train.py "path/to/Churn.csv"

Writes model/beta_bank_attrition_xgb.joblib, model/metadata.json, data/book.parquet (the 2,000 held-out customers
with names, outcome and score), data/customers.parquet (all customers, for the churn map) and data/reference.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost as xgb
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, average_precision_score, f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

from retention.model import AttritionModel
from retention.schema import CATEGORICAL, FEATURES, NUMERICAL

ROOT = Path(__file__).resolve().parent
PARAMS = {  # the notebook's tuned XGBoost (RandomizedSearchCV, 40 combinations, 5-fold AUC-ROC)
    "n_estimators": 800, "learning_rate": 0.01, "max_depth": 6, "min_child_weight": 1, "subsample": 0.9,
    "colsample_bytree": 0.6, "gamma": 0.5, "reg_lambda": 3,
}
# Notebook results that need the full model search (5-fold cross-validation on the training set)
BALANCING = [
    {"Approach": "Threshold moving (no resampling)", "Model": "Gradient boosting", "Best F1": 0.628, "AUC-ROC": 0.865},
    {"Approach": "Undersampling", "Model": "Gradient boosting", "Best F1": 0.622, "AUC-ROC": 0.861},
    {"Approach": "Class weights", "Model": "Random forest", "Best F1": 0.620, "AUC-ROC": 0.859},
    {"Approach": "SMOTE oversampling", "Model": "Gradient boosting", "Best F1": 0.619, "AUC-ROC": 0.861},
]
TUNED = [
    {"Model": "Gradient boosting", "AUC-ROC": 0.8672, "Std": 0.006, "Best F1": 0.631, "File (MB)": 0.3},
    {"Model": "XGBoost (deployed)", "AUC-ROC": 0.8669, "Std": 0.006, "Best F1": 0.629, "File (MB)": 2.4},
    {"Model": "Random forest", "AUC-ROC": 0.8646, "Std": 0.006, "Best F1": 0.623, "File (MB)": 20.0},
]
EARLIER = {"F1": 0.625, "AUC-ROC": 0.860, "Recall": 0.686, "Precision": 0.574, "Mean prediction": 0.33,
           "Brier": 0.125}


def build() -> Pipeline:
    prep = ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
         ("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), NUMERICAL)],
        verbose_feature_names_out=False,
    )
    return Pipeline([("prep", prep), ("model", XGBClassifier(random_state=1, n_jobs=2, eval_metric="logloss", **PARAMS))])


def metrics(y, p, t) -> dict:
    pred = (p >= t).astype(int)
    return {"Accuracy": accuracy_score(y, pred), "Recall": recall_score(y, pred), "Precision": precision_score(y, pred),
            "F1": f1_score(y, pred), "AUC-ROC": roc_auc_score(y, p), "PR-AUC": average_precision_score(y, p)}


def main(csv: Path) -> None:
    df = pd.read_csv(csv)
    X, y = df[FEATURES], df["Exited"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=1)

    pipe = build()
    oof = cross_val_predict(pipe, X_train, y_train, cv=cv, method="predict_proba", n_jobs=5)[:, 1]
    grid = np.round(np.arange(0.05, 0.901, 0.01), 2)
    threshold = float(grid[int(np.argmax([f1_score(y_train, oof >= t) for t in grid]))])
    pipe.fit(X_train, y_train)
    proba = pipe.predict_proba(X_test)[:, 1]
    test = {k: round(float(v), 4) for k, v in metrics(y_test, proba, threshold).items()}

    (ROOT / "model").mkdir(exist_ok=True)
    joblib.dump(pipe, ROOT / "model" / "beta_bank_attrition_xgb.joblib")
    meta = {
        "model": "XGBoost", "threshold": threshold,
        "features": {"categorical": CATEGORICAL, "numerical": NUMERICAL}, "params": PARAMS,
        "cv_auc_roc": round(float(roc_auc_score(y_train, oof)), 4), "test": test,
        "test_rows": int(len(y_test)), "train_rows": int(len(y_train)), "churn_rate": round(float(y.mean()), 4),
        "versions": {"scikit-learn": sklearn.__version__, "xgboost": xgb.__version__, "pandas": pd.__version__,
                     "numpy": np.__version__},
    }
    (ROOT / "model" / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    (ROOT / "data").mkdir(exist_ok=True)
    book = df.loc[X_test.index, ["CustomerId", "Surname"] + FEATURES].copy()
    book["exited"] = y_test.to_numpy()
    book["proba"] = proba
    book.reset_index(drop=True).to_parquet(ROOT / "data" / "book.parquet", index=False)
    df[FEATURES + ["Exited"]].to_parquet(ROOT / "data" / "customers.parquet", index=False)

    model = AttritionModel(ROOT / "model")
    contrib, _ = model.explain(X_test)
    bins = pd.cut(oof, [0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0], include_lowest=True)
    calib = (pd.DataFrame({"p": oof, "y": y_train.to_numpy()}).groupby(bins, observed=True)
             .agg(predicted=("p", "mean"), observed=("y", "mean"), customers=("y", "size")))
    reference = {
        "test": test,
        "importance": {k: round(float(v), 3) for k, v in contrib.abs().mean().sort_values(ascending=False).items()},
        "calibration": {k: [round(float(v), 4) for v in calib[k]] for k in calib.columns},
        "balancing": BALANCING, "tuned": TUNED, "earlier": EARLIER,
    }
    (ROOT / "data" / "reference.json").write_text(json.dumps(reference, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "Churn.csv")
