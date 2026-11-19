"""Cached loaders for the model and the app's data (built by train.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from retention.model import AttritionModel

DATA = Path(__file__).resolve().parent.parent / "data"


@st.cache_resource(show_spinner="Loading the model...")
def model() -> AttritionModel:
    return AttritionModel()


@st.cache_data
def book() -> pd.DataFrame:
    """The 2,000 held-out customers (never seen in training): name, profile, whether they left, and the score."""
    df = pd.read_parquet(DATA / "book.parquet")
    df["at_risk"] = df["proba"] * df["Balance"]
    return df


@st.cache_data
def customers() -> pd.DataFrame:
    """All 10,000 customers and whether they left (for the churn map)."""
    return pd.read_parquet(DATA / "customers.parquet")


@st.cache_data
def reference() -> dict:
    return json.loads((DATA / "reference.json").read_text(encoding="utf-8"))
