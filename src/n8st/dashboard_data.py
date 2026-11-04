"""Export the small tables the dashboard needs into app/data/ (committed to git).

    python -m n8st.dashboard_data

Each export is optional: if an analysis hasn't been run yet, its file is skipped and
the app shows that section as pending.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import polars as pl

from n8st.config import PROCESSED_DIR, PROJECT_ROOT

APP_DATA = PROJECT_ROOT / "app" / "data"


def _export(name: str, df: pl.DataFrame) -> None:
    APP_DATA.mkdir(parents=True, exist_ok=True)
    df.write_csv(APP_DATA / f"{name}.csv")
    print(f"  {name}.csv  {df.height} rows")


def commute() -> None:
    p = PROCESSED_DIR / "commute_replay.parquet"
    if not p.exists():
        return
    r = pl.read_parquet(p)
    opts = {"D": "D to W 4 St", "N_canal": "N, change at Canal", "N_backtrack":
            "N, backtrack from 14 St", "N_walk": "N, walk from Union Sq",
            "N_V1": "N one-seat to 8 St (V1, hypothetical)"}
    rows = [{"option": label, "key": k, "median_min": r[k].median(),
             "p10_min": r[k].quantile(0.1), "p90_min": r[k].quantile(0.9)}
            for k, label in opts.items()]
    _export("commute_options", pl.DataFrame(rows))
    hourly = (r.with_columns(slot=(pl.col("depart_s") // 900 * 900).cast(pl.Int32))
              .group_by("slot").agg(*[pl.col(k).median().alias(k) for k in opts])
              .sort("slot").with_columns(
                  clock=(pl.col("slot") // 3600).cast(pl.String) + ":"
                  + ((pl.col("slot") % 3600) // 60).cast(pl.String).str.zfill(2)))
    _export("commute_by_time", hourly)


def backtrack_wait() -> None:
    p = PROCESSED_DIR / "observed_rw_14st_downtown.parquet"
    if not p.exists():
        return
    obs = pl.read_parquet(p).filter(pl.col("daytype") == "weekday").select(
        "hour", observed_wait_min="expected_wait", p90_gap_min="p90_gap",
        trains_per_hour="trains_per_hour")
    gtfs_zip = PROJECT_ROOT / "data" / "raw" / "gtfs" / "subway_latest.zip"
    if gtfs_zip.exists():
        from n8st.analysis.week1_checks import headways
        from n8st.data import gtfs

        events = gtfs.stop_events(gtfs.load(gtfs_zip))
        sched = (headways(events, "R20", ["R", "W"], "Weekday").filter(pl.col("direction") == "S")
                 .select(pl.col("hour").cast(pl.Int8),
                         scheduled_wait_min=pl.col("expected_wait_min")))
        obs = obs.with_columns(pl.col("hour").cast(pl.Int8)).join(sched, on="hour", how="left")
    _export("backtrack_wait", obs)


def simulation() -> None:
    p = PROCESSED_DIR / "sim_trains.parquet"
    if not p.exists():
        return
    s = pl.read_parquet(p).filter(pl.col("hour").is_between(7, 19))
    piv = s.pivot(on="scenario", index=["day", "direction", "seed", "trip_uid", "route"],
                  values="seconds")
    rows = []
    for scn in [c for c in piv.columns if c in ("V1", "V2")]:
        d = (piv.with_columns(delta=pl.col(scn) - pl.col("base"))
             .group_by("direction", "route").agg(mean_delta_s=pl.col("delta").mean(),
                                                 trains=pl.len())
             .with_columns(scenario=pl.lit(scn)))
        rows.append(d)
    _export("sim_deltas", pl.concat(rows).sort("scenario", "direction", "route"))


def natural_experiment() -> None:
    for name in ("event_study", "ddd_results", "ddd_8st_means"):
        p = PROCESSED_DIR / f"{name}.csv"
        if p.exists():
            _export(name, pl.read_csv(p))


LEDGER_MONTHS = {"weekday_2026_04": "April 2026", "weekday_2026_09": "September 2026",
                 "weekday_2025_10": "October 2025"}
HEADLINE_MONTH = "weekday_2026_04"


def _station_names() -> dict[int, str]:
    p = PROJECT_ROOT / "data" / "raw" / "mta_data" / "bulk" / "stations" / "stations.parquet"
    if not p.exists():
        return {}
    st = pl.read_parquet(p).select(pl.col("complex_id").cast(pl.Float64).cast(pl.Int64),
                                   "stop_name")
    return dict(st.group_by("complex_id").agg(pl.col("stop_name").first()).iter_rows())


def ledger() -> None:
    """Phase-averaged ledger (n8st.ledger.phase_avg) for each month that has been run."""
    from n8st.ledger.run import load_od

    rows, meta = [], {"months": {}}
    for tag, label in LEDGER_MONTHS.items():
        f = PROCESSED_DIR / f"ledger_phase_{tag}"
        if not (f / "totals.csv").exists():
            continue
        m = json.loads((f / "meta.json").read_text())
        n = len(m["offsets_s"])
        rows.append(pl.read_csv(f / "totals.csv").with_columns(
            month=pl.lit(label), month_tag=pl.lit(tag),
            se=pl.col("net_hours_sd_across_offsets") / n ** 0.5))
        od = Path(m["od"])
        m["od_riders_per_day"] = (float(load_od(od)["riders"].sum()) if od.exists()
                                  else None)
        meta["months"][label] = m
    if not rows:
        return
    _export("ledger_totals", pl.concat(rows, how="diagonal_relaxed"))
    head = HEADLINE_MONTH if (PROCESSED_DIR / f"ledger_phase_{HEADLINE_MONTH}" / "totals.csv"
                              ).exists() else rows[0]["month_tag"][0]
    meta["headline_month"] = LEDGER_MONTHS[head]
    APP_DATA.mkdir(parents=True, exist_ok=True)
    (APP_DATA / "ledger_meta.json").write_text(json.dumps(meta, indent=1, default=str))
    f = PROCESSED_DIR / f"ledger_phase_{head}"
    if (f / "by_hour.csv").exists():
        _export("ledger_by_hour", pl.read_csv(f / "by_hour.csv"))
    if (f / "flows.parquet").exists():
        nm = _station_names()
        top = pl.read_parquet(f / "flows.parquet").with_columns(
            origin_name=pl.col("origin").replace_strict(nm, default="?"),
            destination_name=pl.col("destination").replace_strict(nm, default="?"))
        winners = top.sort("hours").group_by("scenario", maintain_order=True).head(15)
        losers = top.sort("hours", descending=True).group_by("scenario",
                                                             maintain_order=True).head(15)
        _export("ledger_top_flows", pl.concat([winners, losers]))


def screen() -> None:
    p = PROCESSED_DIR / f"screen_express_runs_{HEADLINE_MONTH}.csv"
    if p.exists():
        _export("screen_express_runs", pl.read_csv(p))


def forecasting() -> None:
    p = PROCESSED_DIR / "forecast_8st.csv"
    if p.exists():
        _export("forecast_8st", pl.read_csv(p))


def sensitivity() -> None:
    p = PROCESSED_DIR / "sim_sensitivity.parquet"
    if not p.exists():
        return
    r = pl.read_parquet(p).filter(pl.col("baseline_error_pct") <= 5)
    labels = {"n_down_s": "N downtown", "n_up_s": "N uptown",
              "rw_knock_on_s": "R/W knock-on", "q_relief_s": "Q relief"}
    _export("sim_sensitivity", pl.DataFrame([
        {"effect": lab, "p10_s": r[k].quantile(0.1), "median_s": r[k].median(),
         "p90_s": r[k].quantile(0.9), "parameter_sets": r.height}
        for k, lab in labels.items()]))


def wolk() -> None:
    src = PROJECT_ROOT / "docs" / "findings" / "phase0_wolk_replication.md"
    if src.exists():
        APP_DATA.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, APP_DATA / "phase0_wolk_replication.md")


def main() -> None:
    print(f"exporting to {APP_DATA}")
    for fn in (commute, backtrack_wait, simulation, sensitivity, natural_experiment, ledger,
               screen, forecasting, wolk):
        fn()


if __name__ == "__main__":
    main()
