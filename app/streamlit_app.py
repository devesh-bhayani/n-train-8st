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
meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
totals = load("ledger_totals")
BASE_W = "w2_k2_x5"
LABELS = {
    "V1_sim": "V1 · local 34 St–Canal, simulation timing",
    "V1_sched": "V1 · local, weekend-schedule timing",
    "V1_obs": "V1 · local, observed local timing",
    "V2_sched": "V2 · express to 14 St, then 8 St + Prince (schedule timing)",
    "V2_obs": "V2 · express to 14 St, then local (observed timing)",
    "V6_W": "V6 · no stop change: 8 more Sea Beach W trips",
}
ESTIMATES = {
    "net_hours": "Riders keep today's stations",
    "net_hours_flex_calibrated": "Switching, calibrated to the weekend N",
    "net_hours_flex_upper": "Everyone switches to their best station (upper bound)",
}


def rnd(v) -> int | None:
    return None if v is None or pd.isna(v) else int(round(v))


def hours(v: float) -> str:
    return f"{abs(v):,.0f} h {'saved' if v < 0 else 'lost'}"


# --------------------------------------------------------------------------- headline
st.header("The verdict")
if totals is not None:
    month = meta.get("headline_month", totals["month"].iloc[0])
    tm = totals[totals["month"] == month]
    base = tm[tm["weights"] == BASE_W].set_index("scenario")
    head = "V1_sim" if "V1_sim" in base.index else base.index[0]
    r = base.loc[head]
    net, se = r["net_hours"], r["se"]
    verb = "saves" if net < 0 else "costs"
    st.markdown(
        f"<div style='font-family:{FONT};font-size:56px;font-weight:600;color:{INK};"
        f"line-height:1.1'>{abs(net):,.0f} rider-hours</div>"
        f"<div style='color:{INK2};font-size:16px;margin-bottom:16px'>"
        f"per weekday that a local N via 8 St–NYU <b>{verb}</b> riders overall, "
        f"± {2 * se:,.0f} (two standard errors). {month} origin–destination data, "
        "simulation-timed V1, base weights, riders keep today's stations, averaged over "
        "ten timetable alignments of the N.</div>",
        unsafe_allow_html=True)
    c = st.columns(4)
    c[0].metric("Hours saved by those who gain", f"{r['hours_saved']:,.0f}")
    c[1].metric("Hours lost by those slowed", f"{r['hours_lost']:,.0f}")
    if "net_hours_flex_calibrated" in r:
        c[2].metric("With switching, calibrated", hours(r["net_hours_flex_calibrated"]))
        c[3].metric("Switching upper bound", hours(r["net_hours_flex_upper"]))
    st.caption(
        "Switching: riders bound for (or leaving) the 13 stations around Washington Square "
        "may change station. The upper bound lets everyone take their cheapest station; "
        "the calibrated estimate scales that benefit to the switching actually seen on "
        "weekends, when the N already stops at 8 St.")

    st.subheader("Against the pre-registered rule")
    st.markdown(
        "The draft pre-registration (committed before any scenario was scored) says a "
        "scenario supports the change only if **(1)** it saves time at base weights, "
        "**(2)** it saves time in at least 75% of the weight grid, and **(3)** the R/W "
        "knock-on stays under 60 s per train. The simulation puts (3) at about 10 s, so it "
        "passes; (1) and (2) are below, using today's stations as pre-registered.")
    rows = []
    for s in [k for k in LABELS if k in base.index]:
        g = tm[tm["scenario"] == s]
        b = base.loc[s]
        cells = int((g["net_hours"] < 0).sum())
        rows.append({
            "Scenario": LABELS[s],
            "Net (h)": rnd(b["net_hours"]),
            "± 2 se": rnd(2 * b["se"]),
            "Cells saving": f"{cells} of {len(g)}",
            "Rule 1": "pass" if b["net_hours"] < 0 else "fail",
            "Rule 2": "pass" if cells >= 0.75 * len(g) else "fail",
            "Calibrated switching (h)": rnd(b.get("net_hours_flex_calibrated")),
            "Upper bound (h)": rnd(b.get("net_hours_flex_upper")),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.caption("Net (h): riders keep today's stations, as pre-registered. "
               "Negative = riders save time. A net within ± 2 se of zero is not "
               "distinguishable from no effect at this resolution. Rule 3 was simulated for "
               "V1 only. V6 adds eight train trips, an operating cost the ledger can't see.")

    months = totals[(totals["weights"] == BASE_W)
                    & (totals["scenario"].isin(["V1_sim", "V2_sched"]))]
    if months["month"].nunique() > 1:
        st.subheader("Does it hold in other months?")
        m = months.assign(Scenario=months["scenario"].map(LABELS))[
            ["Scenario", "month", "net_hours", "se", *[c for c in ESTIMATES if c != "net_hours"
                                                        and c in months]]].round(0)
        st.dataframe(m.rename(columns={"month": "OD month", "net_hours": "Net, today's stations",
                                       "net_hours_flex_calibrated": "Calibrated switching",
                                       "net_hours_flex_upper": "Upper bound"}),
                     hide_index=True, use_container_width=True)
else:
    st.info("The scenario ledger is still running. The sections below are complete.")

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
    est = st.radio("Estimate", [k for k in ESTIMATES if k in tm], horizontal=True,
                   format_func=ESTIMATES.get)
    head_grid = tm[tm["scenario"] == head]
    piv = head_grid[head_grid["transfer_min"] <= 15].pivot_table(
        index="wait_w", columns="transfer_min", values=est)
    lim = float(abs(piv.values).max())
    fig = go.Figure(go.Heatmap(
        z=piv.values, x=[f"{c:g} min" for c in piv.columns], y=[f"{r:g}×" for r in piv.index],
        colorscale=[[0, DIV_NEG], [0.5, DIV_MID], [1, DIV_POS]], zmin=-lim, zmax=lim,
        texttemplate="%{z:,.0f}", textfont=dict(color=INK), xgap=2, ygap=2,
        hovertemplate="waiting/walking %{y}, transfer %{x}<br>%{z:,.0f} rider-hours"
                      "<extra></extra>", colorbar=dict(title="hours")))
    fig.update_xaxes(title="Penalty per transfer")
    fig.update_yaxes(title="Weight on waiting and walking")
    st.plotly_chart(style(fig, 300), use_container_width=True, theme=None)
    st.caption(f"{LABELS.get(head, head)}, {month}. Blue = riders save time overall; red = "
               "riders lose time overall. The 13th cell (30-minute transfer penalty) is in "
               "the table.")
    table(tm)

    bh = load("ledger_by_hour")
    if bh is not None:
        b = bh[(bh["scenario"] == head) & (bh["weights"] == BASE_W)]
        fig = go.Figure(go.Bar(
            x=b["hour"], y=b["net_hours"], width=0.6,
            marker=dict(color=[DIV_POS if v > 0 else DIV_NEG for v in b["net_hours"]]),
            hovertemplate="%{x}:00 · %{y:,.0f} rider-hours<extra></extra>"))
        fig.update_xaxes(title="Hour of day", dtick=2)
        fig.update_yaxes(title="Net rider-hours (negative = saved)")
        st.subheader("By hour of the day")
        st.plotly_chart(style(fig, 300), use_container_width=True, theme=None)
        st.caption("Riders keep today's stations; base weights; averaged over the ten "
                   "timetable alignments.")
        table(b)

    tf = load("ledger_top_flows")
    if tf is not None:
        t = tf[tf["scenario"] == head].rename(columns={
            "origin_name": "From", "destination_name": "To", "riders": "Riders affected",
            "hours": "Net hours"}).round(0)
        st.subheader("Who wins and who loses")
        c1, c2 = st.columns(2)
        c1.markdown("**Biggest winners**")
        c1.dataframe(t.sort_values("Net hours").head(10)[
            ["From", "To", "Riders affected", "Net hours"]], hide_index=True)
        c2.markdown("**Biggest losers**")
        c2.dataframe(t.sort_values("Net hours", ascending=False).head(10)[
            ["From", "To", "Riders affected", "Net hours"]], hide_index=True)

# --------------------------------------------------------------------------- screen
sc = load("screen_express_runs")
if sc is not None:
    st.header("System-wide: which express runs would be worth running local?")
    st.markdown(
        f"Every weekday express stretch in the subway ({len(sc)} of them) turned local in "
        "turn, timed with the local route's own schedule and scored with the same ledger "
        "(today's stations, base weights, each route averaged over four timetable "
        "alignments). This is a screen: track feasibility is not checked.")
    sc = sc.assign(
        label=sc["route"] + " " + sc["direction"].map({"S": "south", "N": "north"}).fillna("")
        + " · " + sc["from"] + " → " + sc["to"])
    best = sc.sort_values("net_hours_w2_k2_x5").head(12)
    ref = sc[(sc["route"] == "N") & ~sc.index.isin(best.index)]
    show = pd.concat([best, ref]).sort_values("net_hours_w2_k2_x5", ascending=False)
    vals = show["net_hours_w2_k2_x5"]
    fig = go.Figure(go.Scatter(
        x=vals, y=show["label"], mode="markers",
        marker=dict(size=10, color=[DIV_NEG if v < 0 else DIV_POS for v in vals],
                    line=dict(width=2, color="rgba(0,0,0,0)")),
        error_x=dict(type="data", array=2 * show["se"], color=MUTED, thickness=1.5, width=0),
        customdata=show[["stops_added", "se", "added_stations"]],
        hovertemplate="%{y}<br>%{x:,.0f} rider-hours ± %{customdata[1]:,.0f} (1 se)"
                      "<br>%{customdata[0]} stops: %{customdata[2]}<extra></extra>"))
    fig.add_vline(x=0, line=dict(color=AXIS, width=1))
    fig.update_xaxes(title="Net rider-hours per weekday (negative = saved), ± 2 se")
    fig.update_yaxes(showgrid=False, tickfont=dict(color=INK2))
    st.plotly_chart(style(fig, 80 + 28 * len(show)), use_container_width=True, theme=None)
    st.caption("The 12 most promising stretches, plus the N's own (34 St–Canal) for "
               "reference.")
    table(sc.drop(columns=["label"]), "All stretches")

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
    "- **Stations.** The pre-registered ledger keeps every rider's origin and destination "
    "station, so people who would switch from W 4 St or Union Square to 8 St are not "
    "counted, which understates the benefit. The switching estimates relax that around "
    "campus only; the calibrated one leans on a single natural experiment (the weekend N).\n"
    "- **Timetable luck.** Shifting the N by a few minutes with nothing else changed moves "
    "the ledger by ±1,000–2,600 rider-hours, because it changes how N trains interleave "
    "with the W, Q and R. Every result here is averaged over ten alignments of the N "
    "(−9 to +9 min around today's timetable) in both worlds; ± 2 se is the remaining "
    "uncertainty from that.\n"
    "- **Timing.** The extra time for N riders comes from the calibrated simulation "
    "(185 s downtown, 110 s uptown), cross-checked against observed weekday local running "
    "(about 210 s).\n"
    "- **Track layout.** Only the full local pattern (V1) is known to be possible. A "
    "shorter version (V2) needs a crossover between 14 St and 8 St that no source "
    "confirms.\n"
    f"- Full method notes: [docs/how-it-works.md]({REPO}/blob/main/docs/how-it-works.md).")
for label, m in meta.get("months", {}).items():
    if m.get("od_riders_per_day"):
        st.caption(f"Ledger input ({label}): {Path(m['od']).name}, "
                   f"{m['od_riders_per_day']:,.0f} weekday trips, riders sampled every "
                   f"{m['step_s'] // 60} min, N offsets {m['offsets_s'][0]}–"
                   f"{m['offsets_s'][-1]} s.")
