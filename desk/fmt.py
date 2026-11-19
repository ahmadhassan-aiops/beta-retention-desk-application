"""Plain-language values for the model's features."""

from __future__ import annotations

import pandas as pd

SHORT = {
    "Geography": "Country", "Gender": "Gender", "CreditScore": "Credit score", "Age": "Age", "Tenure": "Tenure",
    "Balance": "Balance", "NumOfProducts": "Products", "HasCrCard": "Credit card", "IsActiveMember": "Activity",
    "EstimatedSalary": "Salary",
}


def value(feature: str, v) -> str:
    if feature in ("Balance", "EstimatedSalary"):
        return f"{v:,.0f}"
    if feature == "Tenure":
        return "unknown" if pd.isna(v) else f"{v:.0f} yrs"
    if feature == "IsActiveMember":
        return "active" if v else "inactive"
    if feature == "HasCrCard":
        return "yes" if v else "no"
    if feature == "NumOfProducts":
        return f"{int(v)} product{'s' if int(v) > 1 else ''}"
    if feature in ("Age", "CreditScore"):
        return f"{int(v)}"
    return str(v)


def reason(feature: str, v) -> str:
    """Short tag for a feature that raises the risk, e.g. 'Age 54', 'inactive', '3 products', 'Germany'."""
    if feature in ("Geography", "IsActiveMember", "NumOfProducts"):
        return value(feature, v)
    if feature == "Gender":
        return str(v).lower()
    return f"{SHORT[feature]} {value(feature, v)}"
