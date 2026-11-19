"""The shipped model, metadata, explanations, levers and validation agree. Run: pytest -q"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import f1_score, roc_auc_score

from desk.data import DATA
from retention.model import AttritionModel
from retention.schema import FEATURES, Customer, validate_rows

LOYAL = dict(Geography="France", Gender="Male", CreditScore=700, Age=32, Tenure=5, Balance=0, NumOfProducts=2,
             HasCrCard=1, IsActiveMember=1, EstimatedSalary=90000)
AT_RISK = dict(Geography="Germany", Gender="Female", CreditScore=600, Age=55, Tenure=3, Balance=120000, NumOfProducts=3,
               HasCrCard=1, IsActiveMember=0, EstimatedSalary=90000)


@pytest.fixture(scope="module")
def model() -> AttritionModel:
    return AttritionModel()


@pytest.fixture(scope="module")
def book() -> pd.DataFrame:
    return pd.read_parquet(DATA / "book.parquet")


def test_meets_the_brief(model):
    assert model.meta["test"]["F1"] >= 0.59
    assert model.meta["test"]["AUC-ROC"] > 0.85


def test_shipped_scores_reproduce(model, book):
    assert np.allclose(model.predict_proba(book), book["proba"], atol=1e-6)
    assert f1_score(book["exited"], book["proba"] >= model.threshold) == pytest.approx(model.meta["test"]["F1"], abs=1e-4)
    assert roc_auc_score(book["exited"], book["proba"]) == pytest.approx(model.meta["test"]["AUC-ROC"], abs=1e-4)


def test_shap_adds_up(model, book):
    rows = book.head(40)
    contrib, bias = model.explain(rows)
    assert np.allclose(1 / (1 + np.exp(-(contrib.sum(axis=1).to_numpy() + bias))), model.predict_proba(rows), atol=1e-5)


def test_profiles_and_status(model):
    low, high = model.predict_proba(Customer(**LOYAL).to_frame())[0], model.predict_proba(Customer(**AT_RISK).to_frame())[0]
    assert low < 0.1 < 0.6 < high
    assert model.status(low) == "Stable" and model.status(high) == "Act"


def test_missing_tenure_is_accepted(model):
    p = model.predict_proba(Customer(**{**LOYAL, "Tenure": None}).to_frame())[0]
    assert 0 <= p <= 1


def test_levers_lower_the_risk_for_an_inactive_three_product_customer(model):
    levers = model.levers(Customer(**AT_RISK).to_frame())
    by = {lv["feature"]: lv for lv in levers}
    assert {"IsActiveMember", "NumOfProducts", "all"} <= set(by)
    assert by["NumOfProducts"]["after"] < by["NumOfProducts"]["before"]
    assert by["IsActiveMember"]["after"] < by["IsActiveMember"]["before"]
    assert levers == sorted(levers, key=lambda lv: lv["change"])


def test_no_levers_for_a_fully_engaged_customer(model):
    assert model.levers(Customer(**LOYAL).to_frame()) == []


def test_validation():
    with pytest.raises(ValueError):
        Customer(**{**LOYAL, "Geography": "Italy"})
    raw = pd.DataFrame([LOYAL, {**LOYAL, "NumOfProducts": 7}, AT_RISK])
    clean, errors = validate_rows(raw)
    assert len(clean) == 2 and list(clean.columns) == FEATURES
    assert errors and errors[0].startswith("Row 2: Products held")
    assert validate_rows(raw.drop(columns=["Age"]))[1] == ["Missing column(s): Age"]
