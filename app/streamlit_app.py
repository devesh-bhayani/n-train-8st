"""Should the N stop at 8 St–NYU?  An interactive summary of the project's results.

    uv run --extra app streamlit run app/streamlit_app.py

Reads only the small CSVs in app/data/ (refresh them with `make dashboard-data`), so it
deploys as-is on Streamlit Community Cloud.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data"
REPO = "https://github.com/devesh-bhayani/n-train-8st"

st.set_page_config(page_title="Should the N stop at 8 St–NYU?", page_icon="🚇",
                   layout="wide")

# ---------------------------------------------------------------- palette (dataviz skill)
DARK = getattr(getattr(st.context, "theme", None), "type", "light") == "dark"
if DARK:
    S1, S2, S3 = "#3987e5", "#d95926", "#199e70"
    INK, INK2, MUTED = "#f0efec", "#c3c2b7", "#898781"
    GRID, AXIS, GRAY = "#2c2c2a", "#383835", "#5c5b56"
    DIV_NEG, DIV_POS, DIV_MID = "#3987e5", "#e66767", "#383835"
else:
    S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
    INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
    GRID, AXIS, GRAY = "#e1e0d9", "#c3c2b7", "#b5b4ad"
    DIV_NEG, DIV_POS, DIV_MID = "#2a78d6", "#e34948", "#f0efec"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def load(name: str) -> pd.DataFrame | None:
    p = DATA / f"{name}.csv"
    return pd.read_csv(p) if p.exists() else None


def style(fig: go.Figure, height: int, legend: bool = False) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=8, r=24, t=36 if legend else 12, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=INK2, size=13), showlegend=legend,
        legend=dict(orientation="h", x=0, y=1.12, font=dict(color=INK2)),
        hoverlabel=dict(font_family=FONT), barcornerradius=4,
    )
    for ax in (fig.update_xaxes, fig.update_yaxes):
        ax(gridcolor=GRID, gridwidth=1, linecolor=AXIS, zerolinecolor=AXIS, automargin=True,
           tickfont=dict(color=MUTED), title_font=dict(color=INK2), title_standoff=10)
    return fig


def table(df: pd.DataFrame, label: str = "Table view") -> None:
    with st.expander(label):
        st.dataframe(df, hide_index=True, use_container_width=True)


# ---------------------------------------------------------------------------- header
st.title("Should the N stop at 8 St–NYU?")
st.markdown(
    "On weekdays the N runs express past **8 St–NYU**, the closest station to NYU's "
    "Washington Square campus. On weekends it already stops there, using crossovers "
    "south of Prince St. This project tests whether a weekday stop would save riders "
    "time overall, using MTA ridership and origin–destination data, two months of "
    "observed trains, a routing engine, a calibrated simulation of the Broadway line and "
    f"a natural experiment from 2016. Code and method: [{REPO.split('/')[-1]}]({REPO})."
)

meta_path = DATA / "ledger_meta.json"
totals = load("ledger_totals")

# --------------------------------------------------------------------------- headline
st.header("The verdict, so far")
if totals is not None:
    base = totals[totals["weights"] == "w2_k2_x5"].set_index("scenario")
    head = "V1_sim" if "V1_sim" in base.index else base.index[0]
    net = base.loc[head, "net_hours"]
    verb = "saves" if net < 0 else "costs"
    st.markdown(
        f"<div style='font-family:{FONT};font-size:56px;font-weight:600;color:{INK};"
        f"line-height:1.1'>{abs(net):,.0f} rider-hours</div>"
        f"<div style='color:{INK2};font-size:16px;margin-bottom:16px'>"
        f"per weekday that a local N via 8 St–NYU <b>{verb}</b> riders overall "
        "(simulation-timed V1, base weights; riders keep today's stations)</div>",
        unsafe_allow_html=True)
    c = st.columns(4)
    c[0].metric("Hours saved by those who gain", f"{base.loc[head, 'hours_saved']:,.0f}")
    c[1].metric("Hours lost by those slowed", f"{base.loc[head, 'hours_lost']:,.0f}")
    grid = totals[totals["scenario"] == head]
    c[2].metric("Weight settings where it saves time",
                f"{(grid['net_hours'] < 0).sum()} of {len(grid)}")
    c[3].metric("Riders whose trip changes", f"{base.loc[head, 'riders_affected']:,.0f}")
else:
    st.info("The scenario ledger is still running on the September 2026 origin–destination "
            "data. The sections below are complete.")

# --------------------------------------------------------------------------- commute
st.header("One commute: 18 Av & 72 St to campus")
co = load("commute_options")
if co is not None:
    st.markdown(
        "Every 2-minute departure between 6:30 and 10:30 am on 43 weekdays, replayed on the "
        "trains that actually ran (subwaydata.nyc, Sep–Nov 2026), door to campus.")
    co = co.sort_values("median_min")
    hypo = co["key"] == "N_V1"
    fig = go.Figure(go.Bar(
        x=co["median_min"], y=co["option"], orientation="h",
        marker=dict(color=[S1 if h else GRAY for h in hypo], line=dict(width=0)),
        text=[f"{m:.1f} min" for m in co["median_min"]], textposition="outside",
        textfont=dict(color=INK2), cliponaxis=False, width=0.5,
        customdata=co[["p10_min", "p90_min"]],
        hovertemplate="%{y}<br>median %{x:.1f} min<br>best 10%: %{customdata[0]:.1f}"
                      " · worst 10%: %{customdata[1]:.1f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(title="Median minutes, door to campus",
                     range=[0, co["median_min"].max() * 1.15])
    st.plotly_chart(style(fig, 280), use_container_width=True, theme=None)
    st.caption("Blue: the hypothetical one-seat N (V1). Gray: what runs today.")
    table(co.drop(columns="key"))

bw = load("backtrack_wait")
if bw is not None:
    st.subheader("The 14 St backtrack: waiting for a downtown R or W")
    bw = bw[(bw["hour"] >= 6) & (bw["hour"] <= 23)]
    fig = go.Figure()
    for col, name, color in (("observed_wait_min", "Observed (Sep–Nov 2026)", S1),
                             ("scheduled_wait_min", "Timetable", S2)):
        if col in bw:
            fig.add_trace(go.Scatter(
                x=bw["hour"], y=bw[col], name=name, mode="lines",
                line=dict(color=color, width=2, shape="spline"),
                hovertemplate=f"{name}<br>%{{x}}:00 · %{{y:.1f}} min<extra></extra>"))
            last = bw.dropna(subset=[col]).iloc[-1]
            fig.add_annotation(x=last["hour"], y=last[col], text=name.split(" (")[0],
                               showarrow=False, xanchor="left", xshift=8,
                               font=dict(color=INK2))
    fig.update_xaxes(title="Hour of day", dtick=2)
    fig.update_yaxes(title="Average wait for a random arrival (min)", rangemode="tozero")
    st.plotly_chart(style(fig, 320, legend=True), use_container_width=True, theme=None)
    table(bw)

# --------------------------------------------------------------------------- simulation
sd = load("sim_deltas")
if sd is not None:
    st.header("What a local N does to the other trains")
    st.markdown(
        "A SimPy model of every train between 57 St–7 Av and Canal St, replaying 44 real "
        "weekdays and calibrated to observed running times (median error about 2%). Bars "
        "show the average change per train under V1, against the same day without it.")
    v1 = sd[sd["scenario"] == "V1"].copy()
    v1["label"] = v1["route"] + " · " + v1["direction"].map({"S": "downtown", "N": "uptown"})
    v1 = v1.sort_values("mean_delta_s")
    fig = go.Figure(go.Bar(
        x=v1["mean_delta_s"], y=v1["label"], orientation="h", width=0.5,
        marker=dict(color=[DIV_POS if v > 0 else DIV_NEG for v in v1["mean_delta_s"]]),
        text=[f"{v:+.0f} s" for v in v1["mean_delta_s"]], textposition="outside",
        textfont=dict(color=INK2), cliponaxis=False,
        hovertemplate="%{y}<br>%{x:+.0f} s per train<extra></extra>"))
    fig.update_xaxes(title="Seconds per train vs today (red = slower, blue = faster)",
                     zeroline=True, zerolinewidth=1)
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(style(fig, 360), use_container_width=True, theme=None)
    table(sd)
    ss = load("sim_sensitivity")
    if ss is not None:
        n = int(ss["parameter_sets"].iloc[0])
        st.markdown(
            f"**How sure is this?** Across {n} parameter sets that still reproduce real trains "
            "within 5% (a Gaussian-process surrogate and Sobol indices pick out which "
            "assumptions matter), the effects stay in these ranges:")
        st.dataframe(ss.drop(columns="parameter_sets").round(0), hide_index=True)

# --------------------------------------------------------------------------- ledger
if totals is not None:
    st.header("Robustness: does the answer depend on the assumptions?")
    head_grid = totals[totals["scenario"] == head]
    piv = head_grid.pivot_table(index="wait_w", columns="transfer_min", values="net_hours")
    lim = float(abs(piv.values).max())
    fig = go.Figure(go.Heatmap(
        z=piv.values, x=[f"{c:g} min" for c in piv.columns], y=[f"{r:g}×" for r in piv.index],
        colorscale=[[0, DIV_NEG], [0.5, DIV_MID], [1, DIV_POS]], zmin=-lim, zmax=lim,
        texttemplate="%{z:,.0f}", textfont=dict(color=INK),
        hovertemplate="waiting/walking %{y}, transfer %{x}<br>%{z:,.0f} rider-hours"
                      "<extra></extra>", colorbar=dict(title="hours")))
    fig.update_xaxes(title="Penalty per transfer")
    fig.update_yaxes(title="Weight on waiting and walking")
    st.plotly_chart(style(fig, 300), use_container_width=True, theme=None)
    st.caption("Blue = riders save time overall; red = riders lose time overall.")
    table(totals)

    bh = load("ledger_by_hour")
    if bh is not None:
        b = bh[(bh["scenario"] == head) & (bh["weights"] == "w2_k2_x5")]
        fig = go.Figure(go.Bar(
            x=b["hour"], y=b["net_hours"], width=0.6,
            marker=dict(color=[DIV_POS if v > 0 else DIV_NEG for v in b["net_hours"]]),
            hovertemplate="%{x}:00 · %{y:,.0f} rider-hours<extra></extra>"))
        fig.update_xaxes(title="Hour of day", dtick=2)
        fig.update_yaxes(title="Net rider-hours (negative = saved)")
        st.subheader("By hour of the day")
        st.plotly_chart(style(fig, 300), use_container_width=True, theme=None)

    tf = load("ledger_top_flows")
    if tf is not None:
        t = tf[tf["scenario"] == head]
        c1, c2 = st.columns(2)
        c1.markdown("**Biggest winners**")
        c1.dataframe(t.sort_values("hours").head(10)[
            ["origin_name", "destination_name", "riders", "hours"]], hide_index=True)
        c2.markdown("**Biggest losers**")
        c2.dataframe(t.sort_values("hours", ascending=False).head(10)[
            ["origin_name", "destination_name", "riders", "hours"]], hide_index=True)

# --------------------------------------------------------------------------- 2016
es = load("event_study")
if es is not None:
    st.header("History: what happened when the N left in 2016")
    st.markdown(
        "On November 7, 2016 the W returned and the weekday N went back to express. "
        "Turnstile counts at 28 St, 23 St, 8 St–NYU and Prince St, against nearby stations "
        "on other lines, with the same weeks of 2015 differenced out.")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(es["week"]) + list(es["week"])[::-1],
        y=list(es["ci_high_pct"]) + list(es["ci_low_pct"])[::-1], fill="toself",
        fillcolor="rgba(42,120,214,0.10)", line=dict(width=0), hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=es["week"], y=es["effect_pct"], mode="lines+markers",
        line=dict(color=S1, width=2), marker=dict(size=8, line=dict(width=2, color="white")),
        hovertemplate="week %{x}: %{y:+.1f}%<extra></extra>"))
    fig.add_vline(x=-0.5, line=dict(color=AXIS, width=1))
    fig.update_xaxes(title="Weeks relative to Nov 7, 2016")
    fig.update_yaxes(title="Change in daily entries + exits (%)", zeroline=True)
    st.plotly_chart(style(fig, 320), use_container_width=True, theme=None)
    dd = load("ddd_results")
    if dd is not None:
        table(dd, "Triple-difference estimates")

# --------------------------------------------------------------------------- forecast
fc = load("forecast_8st")
if fc is not None:
    st.header("Forecasting 8 St–NYU a week ahead")
    st.markdown(
        "One LightGBM model for 47 stations, using only what is known a week earlier "
        "(lags, calendar, an approximate NYU-semester flag, weather). On September–October "
        "2026 it misses total ridership by 7.0% (WAPE), against 9.2% for same-day-last-week. "
        "The band is a split-conformal 90% interval; it covered 82% of days, because it was "
        "calibrated on summer data.")
    fc = fc.sort_values("day")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(fc["day"]) + list(fc["day"])[::-1],
                             y=list(fc["hi"]) + list(fc["lo"])[::-1], fill="toself",
                             fillcolor="rgba(42,120,214,0.10)", line=dict(width=0),
                             hoverinfo="skip", name="90% interval"))
    fig.add_trace(go.Scatter(x=fc["day"], y=fc["pred"], name="Forecast", mode="lines",
                             line=dict(color=S1, width=2),
                             hovertemplate="%{x}<br>forecast %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=fc["day"], y=fc["entries"], name="Actual", mode="lines",
                             line=dict(color=S2, width=2),
                             hovertemplate="%{x}<br>actual %{y:,.0f}<extra></extra>"))
    fig.update_yaxes(title="Daily entries", rangemode="tozero")
    st.plotly_chart(style(fig, 320, legend=True), use_container_width=True, theme=None)
    table(fc)

# --------------------------------------------------------------------------- footer
st.header("Caveats")
st.markdown(
    "- **Fixed stations.** The ledger keeps every rider's origin and destination station, "
    "so people who would switch from W 4 St or Union Square to 8 St are not counted. That "
    "understates the benefit.\n"
    "- **Timing.** The extra time for N riders comes from the calibrated simulation "
    "(185 s downtown, 110 s uptown), cross-checked against observed weekday local running "
    "(about 210 s).\n"
    "- **Track layout.** Only the full local pattern (V1) is known to be possible. A "
    "shorter version needs a crossover between 14 St and 8 St that no source confirms.\n"
    f"- Full method notes: [docs/how-it-works.md]({REPO}/blob/main/docs/how-it-works.md).")
if meta_path.exists():
    meta = json.loads(meta_path.read_text())
    st.caption(f"Ledger input: {Path(meta['od']).name}, "
               f"{meta['od_riders_per_day']:,.0f} weekday trips.")
