"""A Beta Bank customer record: field names, labels, valid values and upload validation."""

from __future__ import annotations

from typing import Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, ValidationError

CATEGORICAL = ["Geography", "Gender"]
NUMERICAL = ["CreditScore", "Age", "Tenure", "Balance", "NumOfProducts", "HasCrCard", "IsActiveMember",
             "EstimatedSalary"]
FEATURES = CATEGORICAL + NUMERICAL
COUNTRIES = ["France", "Germany", "Spain"]
GENDERS = ["Female", "Male"]

LABELS = {
    "Geography": "Country", "Gender": "Gender", "CreditScore": "Credit score", "Age": "Age",
    "Tenure": "Tenure (years)", "Balance": "Balance", "NumOfProducts": "Products held",
    "HasCrCard": "Has a credit card", "IsActiveMember": "Active member", "EstimatedSalary": "Estimated salary",
}


class Customer(BaseModel):
    """One customer as the model sees them. Tenure may be unknown (the pipeline fills it with the median)."""

    model_config = ConfigDict(extra="ignore")

    Geography: Literal["France", "Germany", "Spain"]
    Gender: Literal["Female", "Male"]
    CreditScore: int = Field(ge=300, le=900)
    Age: int = Field(ge=18, le=100)
    Tenure: float | None = Field(default=None, ge=0, le=10)
    Balance: float = Field(ge=0, le=1_000_000)
    NumOfProducts: int = Field(ge=1, le=4)
    HasCrCard: int = Field(ge=0, le=1)
    IsActiveMember: int = Field(ge=0, le=1)
    EstimatedSalary: float = Field(ge=0, le=1_000_000)

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([self.model_dump()])[FEATURES].astype({"Tenure": float})


def validate_rows(raw: pd.DataFrame, max_errors: int = 10) -> tuple[pd.DataFrame, list[str]]:
    """Check every row of an uploaded file. Returns the valid rows (model columns) and readable errors."""
    missing = [c for c in FEATURES if c not in raw.columns]
    if missing:
        return pd.DataFrame(columns=FEATURES), ["Missing column(s): " + ", ".join(missing)]
    rows, keep, errors = [], [], []
    for i, record in enumerate(raw[FEATURES].to_dict("records")):
        try:
            rows.append(Customer(**{k: (None if pd.isna(v) else v) for k, v in record.items()}).model_dump())
            keep.append(raw.index[i])
        except ValidationError as exc:
            if len(errors) < max_errors:
                errors.append(f"Row {i + 1}: " + "; ".join(
                    f"{LABELS.get(e['loc'][0], e['loc'][0]) if e['loc'] else ''}: "
                    f"{'missing' if e['type'] == 'missing' else e['msg']}" for e in exc.errors()))
    return pd.DataFrame(rows, columns=FEATURES, index=keep).astype({"Tenure": float}), errors
