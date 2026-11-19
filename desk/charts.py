"""Plotly charts on the dark console: coral raises the risk / left, teal lowers it / stayed. Figures in mono."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from desk import theme as t

CONFIG = {"displayModeBar": False, "scrollZoom": False}
RAMP = [[0, t.PANEL_2], [0.35, "#5a3a33"], [0.7, "#c9583d"], [1, t.CORAL]]


def show(fig: go.Figure, key: str) -> None:
    st.plotly_chart(fig, theme=None, config=CONFIG, key=key)


def style(fig: go.Figure, height: int = 340, legend: bool = False) -> go.Figure:
    fig.update_layout(
        height=height, paper_bgcolor=t.PANEL, plot_bgcolor=t.PANEL, showlegend=legend,
        font=dict(family=t.FONT, size=13, color=t.MUTED), margin=dict(l=10, r=18, t=18, b=10),
        legend=dict(orientation="h", y=1.04, yanchor="bottom", x=0, font=dict(color=t.MUTED)),
        hoverlabel=dict(bgcolor=t.PANEL_2, bordercolor=t.LINE, font=dict(family=t.MONO, color=t.TEXT, size=12)),
    )
    axis = dict(automargin=True, gridcolor=t.LINE, zeroline=False, linecolor=t.LINE, tickfont=dict(family=t.MONO, color=t.DIM),
                title_font=dict(color=t.MUTED))
    fig.update_xaxes(**axis, showgrid=False)
    fig.update_yaxes(**axis)
    return fig


def _p(x: float) -> str:
    return "<1%" if x < 0.01 else ">99%" if x > 0.99 else f"{x:.0%}"


def waterfall(base: float, steps: list[tuple[str, str, float]], final: float) -> go.Figure:
    """From the average customer's chance to this customer's, one feature at a time (largest effects first), drawn
    horizontally so each fact reads as a line. steps: (label, value text, contribution in log-odds)."""
    logit = np.log(base / (1 - base))
    labels, deltas, texts, hover = ["Average customer"], [base * 100], [_p(base)], ["Starting point"]
    prev = base
    for name, value, c in steps:
        logit += c
        p = 1 / (1 + np.exp(-logit))
        labels.append(f"{name} <span style='color:{t.DIM}'>· {value}</span>")
        deltas.append((p - prev) * 100)
        d = (p - prev) * 100
        texts.append("0 pts" if abs(d) < 0.5 else f"{d:+.0f} pts")
        hover.append(f"{name} = {value}")
        prev = p
    labels.append("<b>This customer</b>")
    deltas.append(final * 100)
    texts.append(_p(final))
    hover.append("Final score")
    fig = go.Figure(go.Waterfall(
        orientation="h", y=labels, x=deltas, measure=["absolute"] + ["relative"] * len(steps) + ["total"], text=texts,
        textposition="outside", textfont=dict(family=t.MONO, color=t.TEXT, size=12), customdata=hover,
        hovertemplate="%{customdata}<br>%{text}<extra></extra>", connector=dict(line=dict(color=t.LINE, width=1)),
        increasing=dict(marker=dict(color=t.CORAL)), decreasing=dict(marker=dict(color=t.TEAL)),
        totals=dict(marker=dict(color=t.BLUE)), cliponaxis=False,
    ))
    style(fig, height=46 * len(labels) + 60)
    fig.update_layout(margin=dict(r=60))
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(family=t.FONT, color=t.TEXT, size=13))
    fig.update_xaxes(title="Chance of leaving", ticksuffix="%", range=[0, 112], showgrid=True, dtick=20)
    return fig


def treemap(df: pd.DataFrame) -> go.Figure:
    """Deposits at risk (probability x balance) by country, then by products held. Colour = average chance of leaving."""
    g = df.groupby(["Geography", "NumOfProducts"]).agg(at_risk=("at_risk", "sum"), p=("proba", "mean"),
                                                       n=("proba", "size")).reset_index()
    g = g[g["at_risk"] > 0]
    ids = list(g["Geography"].unique()) + [f"{a}/{b}" for a, b in zip(g["Geography"], g["NumOfProducts"])]
    parents = [""] * g["Geography"].nunique() + list(g["Geography"])
    labels = list(g["Geography"].unique()) + [f"{b} product{'s' if b > 1 else ''}" for b in g["NumOfProducts"]]
    country = g.groupby("Geography").agg(at_risk=("at_risk", "sum"), n=("n", "sum"))
    cp = df.groupby("Geography")["proba"].mean()
    values = list(country.loc[g["Geography"].unique(), "at_risk"]) + list(g["at_risk"])
    colors = list(cp.loc[g["Geography"].unique()]) + list(g["p"])
    counts = list(country.loc[g["Geography"].unique(), "n"]) + list(g["n"])
    fig = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values, branchvalues="total",
        marker=dict(colors=colors, colorscale=RAMP, cmin=0, cmax=0.8, line=dict(color=t.BG, width=2)),
        customdata=np.array([counts, colors]).T,
        texttemplate="<b>%{label}</b><br>%{value:,.3s} at risk",
        hovertemplate="<b>%{label}</b><br>Deposits at risk %{value:,.0f}<br>%{customdata[0]:,} customers<br>"
                      "Average chance of leaving %{customdata[1]:.0%}<extra></extra>",
        textfont=dict(family=t.MONO, color=t.TEXT),
    ))
    style(fig, height=360)
    fig.update_layout(margin=dict(l=4, r=4, t=4, b=4))
    return fig


def age_lines(df: pd.DataFrame) -> go.Figure:
    """Churn rate by age band, one line per country."""
    band = pd.cut(df["Age"], [17, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 100],
                  labels=["18-25", "26-30", "31-35", "36-40", "41-45", "46-50", "51-55", "56-60", "61-65", "66-70", "71+"])
    fig = go.Figure()
    for country, color in (("Germany", t.CORAL), ("France", t.BLUE), ("Spain", t.AMBER)):
        g = df[df["Geography"] == country].groupby(band[df["Geography"] == country], observed=True)["Exited"].agg(["mean", "size"])
        fig.add_trace(go.Scatter(x=g.index.astype(str), y=g["mean"], name=country, mode="lines+markers",
                                 line=dict(color=color, width=2.5), marker=dict(size=7), customdata=g["size"],
                                 hovertemplate=f"{country} %{{x}}<br>%{{y:.0%}} left (of %{{customdata:,}})<extra></extra>"))
    style(fig, height=340, legend=True)
    fig.update_yaxes(title="Share who left", tickformat=".0%", rangemode="tozero")
    fig.update_xaxes(title="Age")
    return fig


def heat(rates: pd.DataFrame, counts: pd.DataFrame, x_title: str, y_title: str, height: int = 300) -> go.Figure:
    z = rates.to_numpy(dtype=float)
    n = counts.reindex_like(rates).fillna(0).to_numpy(dtype=int)
    text = [[f"<b>{r:.0%}</b><br>{c:,}" if c else "" for r, c in zip(zr, zc)] for zr, zc in zip(z, n)]
    fig = go.Figure(go.Heatmap(
        z=z, x=[str(c) for c in rates.columns], y=[str(i) for i in rates.index], zmin=0, zmax=1, colorscale=RAMP,
        showscale=False, xgap=3, ygap=3, text=text, texttemplate="%{text}", textfont=dict(family=t.MONO, color=t.TEXT, size=12),
        customdata=n, hovertemplate=f"{y_title} %{{y}} · {x_title} %{{x}}<br>%{{z:.0%}} left of %{{customdata:,}}<extra></extra>",
    ))
    style(fig, height=height)
    fig.update_xaxes(title=x_title, type="category")
    fig.update_yaxes(title=y_title, type="category", showgrid=False)
    return fig


def rate_bars(labels: list[str], rates: list[float], counts: list[int], average: float) -> go.Figure:
    colors = [t.CORAL if r > average else t.TEAL for r in rates]
    fig = go.Figure(go.Bar(x=labels, y=rates, marker=dict(color=colors, cornerradius=3), text=[f"{r:.0%}" for r in rates],
                           textposition="outside", textfont=dict(family=t.MONO, color=t.TEXT), cliponaxis=False,
                           customdata=counts, hovertemplate="%{x}<br>%{y:.1%} left of %{customdata:,}<extra></extra>"))
    fig.add_hline(y=average, line=dict(color=t.MUTED, width=1, dash="dot"))
    fig.add_annotation(x=1, xref="paper", y=1.06, yref="paper", text=f"dotted: all customers {average:.0%}",
                       showarrow=False, xanchor="right", font=dict(size=11, color=t.DIM))
    style(fig, height=300)
    fig.update_layout(margin=dict(t=30))
    fig.update_yaxes(tickformat=".0%", rangemode="tozero", title="Share who left")
    fig.update_xaxes(tickfont=dict(family=t.FONT, color=t.TEXT))
    return fig


def threshold_curves(curve: pd.DataFrame, threshold: float, target: float) -> go.Figure:
    fig = go.Figure()
    for col, color in (("F1", t.CORAL), ("Recall", t.TEAL), ("Precision", t.BLUE)):
        fig.add_trace(go.Scatter(x=curve["threshold"], y=curve[col], name=col, mode="lines",
                                 line=dict(color=color, width=3 if col == "F1" else 1.8),
                                 hovertemplate=f"{col} %{{y:.3f}}<extra></extra>"))
    fig.add_hline(y=target, line=dict(color=t.AMBER, width=1, dash="dot"))
    fig.add_annotation(x=0.99, y=target, text=f"F1 target {target}", showarrow=False, xanchor="right", yshift=10,
                       font=dict(color=t.AMBER, size=11, family=t.MONO))
    fig.add_vline(x=threshold, line=dict(color=t.TEXT, width=1.2, dash="dash"))
    style(fig, height=340, legend=True)
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(title="Threshold (act on customers at or above)", range=[0, 1])
    fig.update_yaxes(range=[0, 1.02], title="Held-out customers")
    return fig


def confusion(tn: int, fp: int, fn: int, tp: int) -> go.Figure:
    z = [[tn, fp], [fn, tp]]
    names = [["correct", "contacted, stayed"], ["missed", "caught"]]
    shade = np.sqrt(np.array(z) / max(tn, fp, fn, tp))
    fig = go.Figure(go.Heatmap(z=shade, x=["Left alone", "Contacted"], y=["Stayed", "Left"], zmin=0, zmax=1,
                               colorscale=RAMP, showscale=False, xgap=3, ygap=3, hoverinfo="skip"))
    total = tn + fp + fn + tp
    for r, row in enumerate(["Stayed", "Left"]):
        for c, col in enumerate(["Left alone", "Contacted"]):
            fig.add_annotation(x=col, y=row, showarrow=False, font=dict(family=t.MONO, color=t.TEXT, size=11),
                               text=f"<b>{z[r][c]:,}</b><br>{names[r][c]}<br>{z[r][c] / total:.1%}")
    style(fig, height=320)
    fig.update_yaxes(autorange="reversed", showgrid=False, title="What happened")
    fig.update_xaxes(side="top", title="What the desk did")
    return fig


def roc(fpr: np.ndarray, tpr: np.ndarray, auc: float, point: tuple[float, float]) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Random", line=dict(color=t.DIM, dash="dot"),
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=fpr, y=tpr, mode="lines", name=f"XGBoost (AUC {auc:.3f})", line=dict(color=t.CORAL, width=3),
                             fill="tozeroy", fillcolor="rgba(255,122,89,0.08)",
                             hovertemplate="False alarms %{x:.0%}<br>Leavers caught %{y:.0%}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[point[0]], y=[point[1]], mode="markers", name="Chosen threshold",
                             marker=dict(size=12, color=t.TEXT, line=dict(color=t.BG, width=2))))
    style(fig, height=340, legend=True)
    fig.update_xaxes(title="Share of stayers wrongly flagged", tickformat=".0%", range=[0, 1], showgrid=True)
    fig.update_yaxes(title="Share of leavers caught", tickformat=".0%", range=[0, 1.02])
    return fig


def calibration(pred: list[float], obs: list[float], n: list[int]) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Perfect", line=dict(color=t.DIM, dash="dot"),
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=pred, y=obs, mode="lines+markers", name="This model", line=dict(color=t.TEAL, width=2.5),
                             marker=dict(size=9), customdata=n,
                             hovertemplate="Predicted %{x:.0%}<br>Actually left %{y:.0%}<br>%{customdata:,} customers<extra></extra>"))
    style(fig, height=340, legend=True)
    fig.update_xaxes(title="Predicted chance of leaving", tickformat=".0%", range=[0, 1], showgrid=True)
    fig.update_yaxes(title="Share who actually left", tickformat=".0%", range=[0, 1.02])
    return fig


def importance(labels: list[str], values: list[float]) -> go.Figure:
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker=dict(color=t.BLUE, cornerradius=3),
                           hovertemplate="%{y}<br>%{x:.2f} log-odds<extra></extra>"))
    style(fig, height=28 * len(labels) + 60)
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(family=t.FONT, color=t.TEXT))
    fig.update_xaxes(title="Mean |SHAP| (log-odds)", showgrid=True)
    return fig
