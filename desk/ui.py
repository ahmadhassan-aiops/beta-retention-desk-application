"""Retention Desk components: console page titles, numbered panels, KPI strip, customer cards, LED risk meter, profile
sheet, lever rows, takeaway notes and the footer. Light theme, Space Grotesk headings, JetBrains Mono figures.
Every block of information sits in its own bordered, numbered panel."""

from __future__ import annotations

import html
from contextlib import contextmanager

import streamlit as st

from desk import theme as t
from desk.site import CODE_URL, DATA_CREDIT, LEARN_URL, NOTEBOOK_URL

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root {{ --bg:{t.BG}; --panel:{t.PANEL}; --panel2:{t.PANEL_2}; --line:{t.LINE}; --text:{t.TEXT}; --muted:{t.MUTED};
         --dim:{t.DIM}; --coral:{t.CORAL}; --amber:{t.AMBER}; --teal:{t.TEAL}; --blue:{t.BLUE};
         --mono:{t.MONO}; --display:{t.DISPLAY}; }}
html, body, [data-testid="stAppViewContainer"] {{ font-family: {t.FONT}; }}
.block-container {{ padding-top: 2.2rem; max-width: 1240px; }}
h1, h2, h3 {{ font-family: var(--display); letter-spacing: -0.02em; }}
.msr {{ font-family: 'Material Symbols Rounded'; font-weight: normal; font-style: normal; line-height: 1; display: inline-block;
        -webkit-font-feature-settings: 'liga'; font-feature-settings: 'liga'; -webkit-font-smoothing: antialiased; }}
[data-testid="stSidebar"] {{ border-right: 1px solid var(--line); }}
[data-testid="stAppViewContainer"], [data-testid="stMain"] {{ background: var(--bg); }}
[data-testid="stSidebar"] {{ background: #ffffff; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-color: var(--line) !important; border-radius: 12px !important;
                                              background: var(--panel); box-shadow: 0 1px 2px rgba(20, 26, 34, .05); }}
.st-key-panel {{ margin-bottom: .4rem; }}

/* Page title: breadcrumb, display title, one-line brief */
.crumb {{ font-family: var(--mono); font-size: .72rem; letter-spacing: .14em; text-transform: uppercase; color: var(--dim);
          margin: 0 0 .35rem; }}
.crumb b {{ color: var(--coral); font-weight: 700; }}
.ptitle {{ font-family: var(--display); font-size: 2.05rem; font-weight: 700; color: var(--text); margin: 0; line-height: 1.12; }}
.pbrief {{ color: var(--muted); font-size: 1rem; line-height: 1.6; max-width: 820px; margin: .5rem 0 1.4rem; }}
.pbrief b {{ color: var(--text); font-weight: 600; }}

/* Section label */
.sec {{ display: flex; align-items: baseline; gap: .7rem; margin: .1rem 0 .7rem; border-bottom: 1px solid var(--line);
        padding-bottom: .55rem; }}
.sec-n {{ font-family: var(--mono); color: #fff; background: var(--coral); font-size: .75rem; font-weight: 700;
          border-radius: 5px; padding: .1rem .4rem; }}
.sec-t {{ font-family: var(--display); font-size: 1.2rem; font-weight: 600; color: var(--text); margin: 0; }}
.sec-s {{ color: var(--dim); font-size: .85rem; margin-left: auto; text-align: right; }}

/* KPI strip */
.kpis {{ display: grid; grid-template-columns: repeat(var(--n), minmax(0, 1fr)); gap: 1px; background: var(--line);
         border: 1px solid var(--line); border-radius: 10px; overflow: hidden; margin: 0 0 1.2rem; }}
@media (max-width: 800px) {{ .kpis {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
.kpi {{ background: var(--panel); padding: .85rem 1rem .8rem .95rem; position: relative; }}
.kpi::before {{ content: ""; position: absolute; left: 0; top: .9rem; bottom: .9rem; width: 3px; border-radius: 2px;
               background: var(--c, var(--blue)); }}
.kpi-l {{ font-family: var(--mono); font-size: .68rem; letter-spacing: .12em; text-transform: uppercase; color: var(--dim); margin: 0; }}
.kpi-v {{ font-family: var(--mono); font-size: 1.85rem; font-weight: 700; color: var(--text); margin: .25rem 0 .1rem; line-height: 1.1; }}
.kpi-n {{ font-size: .8rem; color: var(--muted); margin: 0; }}

/* Status pill and chips */
.pill {{ display: inline-flex; align-items: center; gap: .3rem; font-family: var(--mono); font-size: .7rem; font-weight: 700;
         letter-spacing: .1em; text-transform: uppercase; color: var(--c); border: 1px solid var(--c);
         border-radius: 4px; padding: .12rem .45rem; background: color-mix(in srgb, var(--c) 12%, transparent); }}
.pill .msr {{ font-size: 14px; }}
.tag {{ display: inline-block; font-size: .74rem; color: var(--muted); background: var(--panel2); border: 1px solid var(--line);
        border-radius: 4px; padding: .1rem .4rem; margin: .15rem .25rem 0 0; }}
.tag.up {{ color: #9c2f18; background: #fcece7; border-color: #f2c7bb; }}

/* Customer card */
.card-top {{ display: flex; justify-content: space-between; align-items: flex-start; gap: .5rem; }}
.c-name {{ font-family: var(--display); font-size: 1.12rem; font-weight: 600; color: var(--text); margin: 0; }}
.c-id {{ font-family: var(--mono); font-size: .72rem; color: var(--dim); margin: .1rem 0 0; }}
.c-row {{ display: flex; align-items: baseline; gap: 1.1rem; margin: .7rem 0 .35rem; }}
.c-p {{ font-family: var(--mono); font-size: 2rem; font-weight: 700; line-height: 1; color: var(--c); }}
.c-p small {{ font-size: .72rem; color: var(--dim); font-weight: 400; margin-left: .25rem; }}
.c-m {{ font-family: var(--mono); font-size: .95rem; color: var(--text); }}
.c-m small {{ display: block; font-size: .68rem; color: var(--dim); letter-spacing: .08em; text-transform: uppercase; }}

/* LED risk meter */
.leds {{ display: grid; grid-template-columns: repeat(25, minmax(0, 1fr)); gap: 3px; margin: .55rem 0 .3rem; }}
.led {{ height: 20px; border-radius: 2px; background: var(--panel2); border: 1px solid var(--line); }}
.led.on {{ background: var(--c); border-color: var(--c); }}
.led.mark {{ outline: 2px solid var(--text); outline-offset: 1px; }}
.led-scale {{ display: flex; justify-content: space-between; font-family: var(--mono); font-size: .68rem; color: var(--dim); }}
.big-risk {{ font-family: var(--mono); font-size: 3.4rem; font-weight: 700; line-height: 1; color: var(--c); margin: .35rem 0 0; }}
.big-risk small {{ font-family: {t.FONT}; font-size: .95rem; color: var(--muted); font-weight: 500; margin-left: .5rem; }}

/* Profile sheet */
.sheet {{ display: grid; grid-template-columns: auto 1fr; gap: .35rem 1.2rem; margin: .6rem 0 0; }}
.sheet dt {{ font-family: var(--mono); font-size: .7rem; letter-spacing: .1em; text-transform: uppercase; color: var(--dim);
            padding-top: .15rem; }}
.sheet dd {{ margin: 0; font-family: var(--mono); font-size: .92rem; color: var(--text); }}

/* Lever rows */
.lever {{ display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 2fr) auto; gap: 1rem; align-items: center;
          padding: .7rem 0; border-top: 1px solid var(--line); }}
.lever:first-child {{ border-top: 0; }}
.lv-name {{ font-weight: 600; color: var(--text); margin: 0; font-size: .95rem; }}
.lv-name small {{ display: block; color: var(--dim); font-weight: 400; font-size: .78rem; margin-top: .1rem; }}
.lv-bar {{ position: relative; height: 10px; background: var(--panel2); border-radius: 5px; }}
.lv-from {{ position: absolute; left: 0; top: 0; bottom: 0; border-radius: 5px; background: color-mix(in srgb, var(--coral) 35%, transparent); width: var(--a); }}
.lv-to {{ position: absolute; left: 0; top: 0; bottom: 0; border-radius: 5px; background: var(--teal); width: var(--b); }}
.lv-d {{ font-family: var(--mono); font-weight: 700; font-size: 1rem; color: var(--teal); white-space: nowrap; }}
.lv-d.none {{ color: var(--dim); }}
.lv-d small {{ display: block; font-weight: 400; font-size: .72rem; color: var(--dim); text-align: right; }}
.play {{ border: 1px solid color-mix(in srgb, var(--teal) 55%, transparent); background: color-mix(in srgb, var(--teal) 9%, transparent);
         border-radius: 10px; padding: .85rem 1rem; margin: .4rem 0 .2rem; }}
.play-l {{ font-family: var(--mono); font-size: .68rem; letter-spacing: .14em; text-transform: uppercase; color: var(--teal); margin: 0; }}
.play-t {{ color: var(--text); font-size: .98rem; line-height: 1.55; margin: .3rem 0 0; }}

/* Briefing notes */
.notes {{ counter-reset: n; display: grid; gap: .55rem; margin: .5rem 0 .2rem; background: var(--panel2);
          border: 1px solid var(--line); border-left: 3px solid var(--coral); border-radius: 8px; padding: .75rem .9rem; }}
.note {{ display: grid; grid-template-columns: 2.2rem 1fr; gap: .4rem; align-items: start; color: var(--muted); font-size: .95rem;
         line-height: 1.55; }}
.note::before {{ counter-increment: n; content: counter(n, decimal-leading-zero); font-family: var(--mono); color: var(--coral);
                font-weight: 700; font-size: .85rem; padding-top: .1rem; }}
.note b {{ color: var(--text); font-weight: 600; }}
.caveat {{ color: var(--dim); font-size: .82rem; line-height: 1.5; margin: .4rem 0 0; }}
.caveat b {{ color: var(--muted); }}

/* Target check */
.target {{ display: flex; align-items: center; gap: 1rem; border: 1px solid var(--c); border-radius: 10px; padding: .9rem 1.1rem;
           background: color-mix(in srgb, var(--c) 8%, transparent); margin: 0 0 1.2rem; }}
.target .msr {{ font-size: 34px; color: var(--c); }}
.target-v {{ font-family: var(--mono); font-size: 1.5rem; font-weight: 700; color: var(--text); margin: 0; }}
.target-t {{ color: var(--muted); margin: .15rem 0 0; font-size: .92rem; }}

.foot {{ border-top: 1px solid var(--line); margin-top: 2.6rem; padding-top: 1rem; color: var(--dim); font-size: .82rem; line-height: 1.6; }}
.foot a {{ color: var(--muted); }}
.foot b {{ color: var(--text); }}
</style>
"""


def inject_css() -> None:
    st.html(CSS)


def icon(name: str) -> str:
    return f'<span class="msr" aria-hidden="true">{html.escape(name)}</span>'


def money(x: float) -> str:
    """Compact amount: 1.2M, 84k, 950."""
    if abs(x) >= 1e6:
        return f"{x / 1e6:.1f}M"
    if abs(x) >= 1e3:
        return f"{x / 1e3:.0f}k"
    return f"{x:,.0f}"


def pct(p: float) -> str:
    if p < 0.01:
        return "&lt;1%"
    if p > 0.99:
        return "&gt;99%"
    return f"{p:.0%}"


def title(crumb: str, text: str, brief: str) -> None:
    st.html(f'<p class="crumb">Retention Desk / <b>{html.escape(crumb)}</b></p><h1 class="ptitle">{html.escape(text)}</h1>'
            f'<p class="pbrief">{brief}</p>')


def section(n: str, text: str, sub: str = "") -> None:
    st.html(f'<div class="sec"><span class="sec-n">{html.escape(n)}</span><p class="sec-t">{html.escape(text)}</p>'
            f'<span class="sec-s">{html.escape(sub)}</span></div>')


@contextmanager
def panel(n: str, text: str, sub: str = ""):
    """A bordered panel with a numbered heading; everything inside the `with` block belongs to it."""
    with st.container(border=True):
        section(n, text, sub)
        yield


def kpis(items: list[tuple[str, str, str, str]]) -> None:
    """KPI strip. Each item: (label, value, note, colour)."""
    cells = "".join(f'<div class="kpi" style="--c:{c}"><p class="kpi-l">{html.escape(lab)}</p><p class="kpi-v">{v}</p>'
                    f'<p class="kpi-n">{n}</p></div>' for lab, v, n, c in items)
    st.html(f'<div class="kpis" style="--n:{len(items)}">{cells}</div>')


def pill(status: str) -> str:
    s = t.STATUS[status]
    return f'<span class="pill" style="--c:{s["color"]}">{icon(s["icon"])}{s["label"]}</span>'


def customer_card(name: str, cid: int, country: str, status: str, p: float, balance: float, reasons: list[str]) -> None:
    c = t.STATUS[status]["color"]
    tags = "".join(f'<span class="tag up">{html.escape(r)}</span>' for r in reasons)
    st.html(
        f'<div style="--c:{c}"><div class="card-top"><div><p class="c-name">{html.escape(name)}</p>'
        f'<p class="c-id">#{cid} · {html.escape(country)}</p></div>{pill(status)}</div>'
        f'<div class="c-row"><span class="c-p">{pct(p)}<small>leave</small></span>'
        f'<span class="c-m"><small>Balance</small>{money(balance)}</span>'
        f'<span class="c-m"><small>At risk</small>{money(p * balance)}</span></div><div>{tags}</div></div>'
    )


def led_meter(p: float, threshold: float, status: str, caption: str) -> None:
    """Probability as 25 LEDs (4 points each); the LED holding the act threshold is outlined."""
    c = t.STATUS[status]["color"]
    lit = int(round(p * 25))
    mark = min(24, int(threshold * 25))
    leds = "".join(f'<span class="led{" on" if i < lit else ""}{" mark" if i == mark else ""}"></span>' for i in range(25))
    st.html(f'<div style="--c:{c}"><p class="big-risk">{pct(p)}<small>{html.escape(caption)}</small></p>'
            f'<div class="leds" role="img" aria-label="{pct(p)} chance of leaving">{leds}</div>'
            f'<div class="led-scale"><span>0%</span><span>act from {threshold:.0%} (outlined)</span><span>100%</span></div></div>')


def sheet(rows: list[tuple[str, str]]) -> None:
    st.html('<dl class="sheet">' + "".join(f"<dt>{html.escape(k)}</dt><dd>{html.escape(v)}</dd>" for k, v in rows)
            + "</dl>")


def levers(rows: list[dict]) -> None:
    """Each row: label, before, after, change. Bars show before (faint coral) and after (teal) on a 0-100% scale."""
    out = []
    for r in rows:
        d = r["change"]
        cls = "lv-d" if d <= -0.005 else "lv-d none"
        out.append(
            f'<div class="lever"><p class="lv-name">{html.escape(r["label"])}<small>{pct(r["before"])} → '
            f'{pct(r["after"])}</small></p><div class="lv-bar"><span class="lv-from" style="--a:{r["before"] * 100:.1f}%">'
            f'</span><span class="lv-to" style="--b:{r["after"] * 100:.1f}%"></span></div>'
            f'<span class="{cls}">{d * 100:+.0f} pts<small>chance of leaving</small></span></div>')
    st.html("".join(out))


def play(text: str) -> None:
    st.html(f'<div class="play"><p class="play-l">Recommended play</p><p class="play-t">{text}</p></div>')


def notes(items: list[str]) -> None:
    st.html('<div class="notes">' + "".join(f'<div class="note"><div>{x}</div></div>' for x in items) + "</div>")


def caveat(text: str) -> None:
    st.html(f'<p class="caveat">{text}</p>')


def target(ok: bool, value: str, text: str) -> None:
    c = t.TEAL if ok else t.CORAL
    st.html(f'<div class="target" style="--c:{c}">{icon("task_alt" if ok else "error")}<div><p class="target-v">{value}</p>'
            f'<p class="target-t">{text}</p></div></div>')


def footer() -> None:
    st.html(f'<div class="foot">Model and app by <b>Ahmad Hassan</b>, AI Engineer · <a href="{NOTEBOOK_URL}" target="_blank">'
            f'Notebook</a> · <a href="{CODE_URL}" target="_blank">App code</a> · <a href="{LEARN_URL}" target="_blank">'
            f'Learn with Ahmad</a><br>{DATA_CREDIT}</div>')
