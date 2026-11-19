"""Churn map: where attrition concentrates across all 10,000 customers."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from desk import charts, data, ui


def render() -> None:
    df = data.customers()
    avg = df["Exited"].mean()
    ui.title("Churn map", "Where Beta Bank loses customers",
             f"All {len(df):,} customers, {int(df['Exited'].sum()):,} of whom left ({avg:.1%}). Churn is not spread evenly: "
             "<b>age, the number of products, activity and country</b> separate the leavers from the rest.")
    lost = df.loc[df["Exited"] == 1, "Balance"].sum() / df["Balance"].sum()
    ui.kpis([
        ("Left the bank", f"{avg:.1%}", f"{int(df['Exited'].sum()):,} customers", "#ff7a59"),
        ("Deposits they took", f"{lost:.0%}", "of all balances", "#ff7a59"),
        ("Aged 51 to 60", f"{df.loc[df['Age'].between(51, 60), 'Exited'].mean():.0%}", "left, the riskiest age", "#f2b84b"),
        ("Two products", f"{df.loc[df['NumOfProducts'] == 2, 'Exited'].mean():.1%}", "left, the most loyal group", "#3ec7b0"),
    ])

    ui.section("01", "Age is the strongest pattern", "share who left, by age and country")
    charts.show(charts.age_lines(df), "age")
    ui.notes([
        "Churn is low until 40, then <b>climbs steeply through the 40s and peaks in the 50s</b>, before falling again "
        "after 60. The same shape appears in all three countries.",
        "<b>Germany sits above France and Spain at almost every age</b>: about twice their churn overall (32% against 16 to 17%).",
    ])

    ui.section("02", "Activity decides within each age", "share who left, by age and activity")
    band = pd.cut(df["Age"], [17, 30, 40, 50, 60, 70, 100], labels=["18-30", "31-40", "41-50", "51-60", "61-70", "71+"])
    act = df["IsActiveMember"].map({0: "Inactive", 1: "Active"})
    rates = df.pivot_table(index=act, columns=band, values="Exited", aggfunc="mean", observed=True)
    counts = df.pivot_table(index=act, columns=band, values="Exited", aggfunc="size", observed=True)
    charts.show(charts.heat(rates, counts, "Age", "Member", height=230), "age_act")
    ui.notes(["<b>Inactive customers aged 51 to 70 are the clearest warning sign</b>: almost nine in ten leave. Active customers of "
              "the same age leave far less often, so re-engaging older inactive customers is the most promising lever."])

    a, b = st.columns(2, gap="large")
    with a:
        ui.section("03", "Products: two is the sweet spot")
        g = df.groupby("NumOfProducts")["Exited"].agg(["mean", "size"])
        charts.show(charts.rate_bars([f"{i} product{'s' if i > 1 else ''}" for i in g.index], g["mean"].tolist(),
                                     g["size"].tolist(), avg), "products")
        ui.notes(["One product: 28% leave. <b>Two: 7.6%.</b> Three: 83%. <b>Four: every one of the 60 customers left.</b> "
                  "Three or four products look like bundles that did not fit, not loyalty."])
    with b:
        ui.section("04", "Country and gender")
        labels, rates_, ns = [], [], []
        for col in ("Geography", "Gender"):
            g = df.groupby(col)["Exited"].agg(["mean", "size"])
            labels += list(g.index)
            rates_ += g["mean"].tolist()
            ns += g["size"].tolist()
        charts.show(charts.rate_bars(labels, rates_, ns, avg), "country")
        ui.notes(["Germany loses customers at twice the rate of France and Spain, and German customers hold the largest "
                  "balances. <b>Women leave more often than men</b> (25% against 16.5%)."])

    ui.section("05", "What does not matter much")
    ui.notes(["<b>Credit score, tenure, estimated salary and holding a credit card</b> barely change the churn rate "
              "(within a few points of the average across their ranges). The model gives them little weight too."])
    ui.footer()
