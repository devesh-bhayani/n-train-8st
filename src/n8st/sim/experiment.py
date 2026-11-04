"""Calibrate the Broadway simulation against observed trains, then run scenarios.

    python -m n8st.sim.experiment            # all observed weekdays, both directions
    python -m n8st.sim.experiment --days 5 --seeds 2

Writes docs/findings/simulation.md and data/processed/sim_*.parquet.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import polars as pl

from n8st.analysis import observed as ob
from n8st.config import FINDINGS_DIR, PROCESSED_DIR, RAW_DIR
from n8st.sim import broadway as bw

MONTHLY = RAW_DIR / "mta_data" / "bulk" / "ridership" / "monthly_by_complex.parquet"
STATIONS = RAW_DIR / "mta_data" / "bulk" / "stations" / "stations.parquet"

# Share of a complex's riders using the Broadway platforms (rough: transfer hubs serve
# several lines; transfers in are not counted in entries, so hubs get a boost).
BROADWAY_SHARE = {"R14": 0.8, "R16": 0.35, "R17": 0.5, "R20": 0.7, "R23": 0.6, "Q01": 0.4}
# Weekday share of daily riders in each hour (typical NYC subway profile).
HOUR_PROFILE = {5: 0.015, 6: 0.035, 7: 0.07, 8: 0.09, 9: 0.065, 10: 0.045, 11: 0.045,
                12: 0.05, 13: 0.05, 14: 0.055, 15: 0.065, 16: 0.075, 17: 0.085, 18: 0.07,
                19: 0.05, 20: 0.04, 21: 0.03, 22: 0.025, 23: 0.015}
CORRIDOR = bw.LOCAL_S + ["R23", "Q01"]
# From python -m n8st.sim.calibrate (8 weekdays, 36 parameter sets, 2026-11-04):
# median corridor-time RMSE 2.1 %, 90th percentile 5.2 %, headway CV 0.66 vs 0.59 observed.
CALIBRATED = {"hold": 3, "block_target_s": 45.0, "base_dwell_s": 30.0, "per_pax_s": 0.12,
              "run_noise_sd": 0.08, "incident_prob": 0.02, "incident_mean_s": 90.0}
ENTRY = {"S": {"N": "R14", "Q": "R14", "R": "R14", "W": "R14"},
         "N": {"N": "Q01", "Q": "Q01", "R": "R23", "W": "R23"}}
EXIT = {"S": {"N": "Q01", "Q": "Q01", "R": "R23", "W": "R23"},
        "N": {"N": "R14", "Q": "R14", "R": "R14", "W": "R14"}}


def stop_to_stop(df: pl.DataFrame, q: float = 0.15) -> dict[tuple, float]:
    """Low-quantile observed seconds between consecutive stops, keyed by
    (direction, track_a, station_a, track_b, station_b), weekday daytime."""
    d = (df.filter((pl.col("daytype") == "weekday") & pl.col("hour").is_between(6, 21)
                   & pl.col("route_id").is_in(["N", "Q", "R", "W"])
                   & pl.col("parent").is_in(CORRIDOR))
         .unique(["trip_uid", "stop_id"]).sort("trip_uid", "arr")
         .with_columns(nxt=pl.col("parent").shift(-1).over("trip_uid"),
                       nxt_track=pl.col("track").shift(-1).over("trip_uid"),
                       dt=(pl.col("arr").shift(-1).over("trip_uid") - pl.col("arr"))
                       .dt.total_seconds())
         .drop_nulls(["nxt", "dt"]).filter(pl.col("dt") > 15))
    t = (d.group_by("direction", "track", "parent", "nxt_track", "nxt")
         .agg(n=pl.len(), s=pl.col("dt").quantile(q)).filter(pl.col("n") >= 100))
    return {(a, b, c, e, f): float(s) for a, b, c, e, f, _, s in t.iter_rows()}


def pax_rates(month: str = "2026-09") -> dict[str, float]:
    """Peak-hour boarding+alighting activity per second, per direction, by GTFS station."""
    st = pl.read_parquet(STATIONS).select(
        "gtfs_stop_id", pl.col("complex_id").cast(pl.Float64).cast(pl.Int64))
    m = pl.read_parquet(MONTHLY).with_columns(
        pl.col("station_complex_id").cast(pl.Float64).cast(pl.Int64))
    m = m.filter(pl.col("month").cast(pl.String).str.starts_with(month))
    daily = {c: r / 26 for c, r in m.select("station_complex_id", "ridership").iter_rows()}
    rates = {}
    for g, c in st.filter(pl.col("gtfs_stop_id").is_in(CORRIDOR)).iter_rows():
        e = daily.get(c, 0.0) * BROADWAY_SHARE.get(g, 1.0)
        # entries + exits ~ 2E, half per direction, peak hour share 9%
        rates[g] = e * 0.09 / 3600
    return rates


def entries(df: pl.DataFrame, day, direction: str) -> list[tuple[str, str, float]]:
    """Observed corridor entries for one day: (trip_uid, route, seconds since midnight)."""
    sub = df.filter((pl.col("service_day") == day) & (pl.col("direction") == direction)
                    & pl.col("route_id").is_in(list(ENTRY[direction])))
    out = []
    for route, station in ENTRY[direction].items():
        e = (sub.filter((pl.col("route_id") == route) & (pl.col("parent") == station))
             .sort("arr").unique("trip_uid", keep="first"))
        for uid, t in e.select("trip_uid", "arr").iter_rows():
            secs = t.hour * 3600 + t.minute * 60 + t.second
            if 5 * 3600 <= secs < 24 * 3600:
                out.append((uid, route, float(secs)))
    return out


def observed_corridor(df: pl.DataFrame, day, direction: str) -> pl.DataFrame:
    sub = df.filter((pl.col("service_day") == day) & (pl.col("direction") == direction))
    rows = []
    for route in ENTRY[direction]:
        a = sub.filter((pl.col("route_id") == route)
                       & (pl.col("parent") == ENTRY[direction][route])).select("trip_uid", t0="arr")
        b = sub.filter((pl.col("route_id") == route)
                       & (pl.col("parent") == EXIT[direction][route])).select("trip_uid", t1="arr")
        a = a.sort("t0").unique("trip_uid", keep="first")
        b = b.sort("t1").unique("trip_uid", keep="last")
        j = a.join(b, on="trip_uid").with_columns(
            route=pl.lit(route), seconds=(pl.col("t1") - pl.col("t0")).dt.total_seconds(),
            hour=pl.col("t0").dt.hour())
        rows.append(j.select("trip_uid", "route", "hour", "seconds"))
    return pl.concat(rows).filter(pl.col("seconds") > 0)


def records_frame(recs: list[bw.TrainRecord]) -> pl.DataFrame:
    return pl.DataFrame([
        {"trip_uid": r.train_id, "route": r.route, "hour": int(r.entry_s // 3600),
         "seconds": r.exit_s - r.entry_s} for r in recs if r.stops
    ])


def headway_cv(recs: list[bw.TrainRecord], station: str, track: str,
               hours=(7, 20)) -> float:
    deps = sorted(dep for r in recs for (t, s, _a, dep) in r.stops
                  if s == station and t == track and hours[0] * 3600 <= dep < hours[1] * 3600)
    gaps = np.diff(deps)
    gaps = gaps[gaps < 1800]
    return float(np.std(gaps) / np.mean(gaps)) if len(gaps) > 5 else float("nan")


def run(df: pl.DataFrame, days: list, seeds: int, params: bw.Params, scenarios: list[str]
        ) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    s2s = stop_to_stop(df)
    params.pax_rate = pax_rates()
    params.hour_factor = {h: v / max(HOUR_PROFILE.values()) for h, v in HOUR_PROFILE.items()}
    sims, obs, regularity = [], [], []
    for day in days:
        for direction in ("S", "N"):
            ent = entries(df, day, direction)
            obs.append(observed_corridor(df, day, direction).with_columns(
                day=pl.lit(day), direction=pl.lit(direction)))
            for scenario in scenarios:
                for seed in range(seeds):
                    recs = bw.simulate(ent, direction, scenario, s2s, params, seed=seed)
                    sims.append(records_frame(recs).with_columns(
                        day=pl.lit(day), direction=pl.lit(direction),
                        scenario=pl.lit(scenario), seed=pl.lit(seed)))
                    local = "A1" if direction == "S" else "A2"
                    regularity.append({"day": day, "direction": direction, "scenario": scenario,
                                       "seed": seed,
                                       "cv_14st_local": headway_cv(recs, "R20", local),
                                       "cv_8st": headway_cv(recs, "R21", local)})
        print(f"  simulated {day}", flush=True)
    return pl.concat(sims), pl.concat(obs), pl.DataFrame(regularity)


def md(df: pl.DataFrame, digits: int = 0) -> str:
    df = df.with_columns(pl.col(pl.Float64, pl.Float32).round(digits))
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |"
              for r in df.iter_rows()]
    return "\n".join(lines)


def report(sims: pl.DataFrame, obs: pl.DataFrame, reg: pl.DataFrame, params: bw.Params,
           days: list, seeds: int) -> str:
    day_hours = pl.col("hour").is_between(7, 19)
    base = sims.filter((pl.col("scenario") == "base") & day_hours)
    val = (base.group_by("direction", "route").agg(sim_median=pl.col("seconds").median(),
                                                   sim_p90=pl.col("seconds").quantile(0.9))
           .join(obs.filter(day_hours).group_by("direction", "route").agg(
               obs_median=pl.col("seconds").median(), obs_p90=pl.col("seconds").quantile(0.9),
               trips=pl.len()), on=["direction", "route"])
           .with_columns(error_pct=100 * (pl.col("sim_median") / pl.col("obs_median") - 1))
           .sort("direction", "route"))

    paired = (sims.filter(day_hours)
              .pivot(on="scenario", index=["day", "direction", "seed", "trip_uid", "route"],
                     values="seconds"))
    deltas = []
    for scn in [s for s in sims["scenario"].unique().to_list() if s != "base"]:
        d = (paired.with_columns(delta=pl.col(scn) - pl.col("base"))
             .group_by("direction", "route")
             .agg(mean_delta_s=pl.col("delta").mean(), p90_delta_s=pl.col("delta").quantile(0.9),
                  trains=pl.len())
             .with_columns(scenario=pl.lit(scn)).sort("direction", "route"))
        deltas.append(d)
    deltas_df = pl.concat(deltas).select("scenario", "direction", "route", "trains",
                                         "mean_delta_s", "p90_delta_s")
    regs = (reg.with_columns(pl.col("cv_14st_local", "cv_8st").fill_nan(None))
            .group_by("scenario", "direction").agg(
                pl.col("cv_14st_local").mean(), pl.col("cv_8st").mean())
            .sort("direction", "scenario"))

    out = [
        "# Broadway line simulation (57 St–7 Av to Canal St)",
        "",
        f"SimPy, block-signal model, {len(days)} observed weekdays × {seeds} seeds per scenario, "
        "both directions. Trains enter at the times they were observed entering the corridor; "
        "scenarios reuse the same entries and random numbers.",
        "",
        f"Parameters: hold {params.hold} blocks, block target {params.block_target_s:.0f} s, "
        f"base dwell {params.base_dwell_s:.0f} s, {params.per_pax_s} s per passenger, "
        "passenger rates from September 2026 station ridership (rough).",
        "",
        "## 1. Validation: simulated vs observed corridor time, baseline, 7 am–8 pm",
        "",
        "Seconds from entering the corridor (57 St southbound; Canal northbound) to leaving it.",
        "",
        md(val, 0),
        "",
        "## 2. What each scenario does to each route (seconds per train, vs baseline)",
        "",
        "Same trains, same day, same random numbers. For the N, the delta includes the extra "
        "stops themselves; for the R, W and Q it is pure knock-on delay (or relief).",
        "",
        md(deltas_df, 0),
        "",
        "## 3. Service regularity (headway coefficient of variation, local platforms)",
        "",
        md(regs, 3),
        "",
    ]
    return "\n".join(out)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--days", type=int, default=0, help="0 = all observed weekdays")
    p.add_argument("--seeds", type=int, default=3)
    p.add_argument("--scenarios", nargs="*", default=["base", "V1", "V2"])
    # Defaults = calibrated values (docs/findings/sim_calibration.md).
    p.add_argument("--hold", type=int, default=CALIBRATED["hold"])
    p.add_argument("--block", type=float, default=CALIBRATED["block_target_s"])
    p.add_argument("--per-pax", type=float, default=CALIBRATED["per_pax_s"])
    p.add_argument("--incident-prob", type=float, default=CALIBRATED["incident_prob"])
    p.add_argument("--out", type=Path, default=FINDINGS_DIR / "simulation.md")
    args = p.parse_args()

    df = ob.load()
    days = sorted(df.filter(pl.col("daytype") == "weekday")["service_day"].unique().to_list())
    if args.days:
        days = days[: args.days]
    params = bw.Params(**{**CALIBRATED, "hold": args.hold, "block_target_s": args.block,
                          "per_pax_s": args.per_pax, "incident_prob": args.incident_prob})
    sims, obs, reg = run(df, days, args.seeds, params, args.scenarios)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    sims.write_parquet(PROCESSED_DIR / "sim_trains.parquet")
    reg.write_parquet(PROCESSED_DIR / "sim_regularity.parquet")
    text = report(sims, obs, reg, params, days, args.seeds)
    args.out.write_text(text)
    print(text)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
