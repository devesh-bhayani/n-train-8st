"""What trains actually did: observed headways, waits and running times.

Source: subwaydata.nyc daily archives (built from the MTA's GTFS-realtime feeds), pulled
by the fetch-data workflow into the mta-data branch:

    make mta-pull
    python -m n8st.analysis.observed

Times in subwaydata.nyc are the last real-time prediction before a train was marked as
having passed a stop, so they are accurate to roughly the 30 s feed refresh. Arrival and
departure are usually identical (no dwell). Implausibly fast segments are dropped.

Writes docs/findings/observed_service.md and data/processed/observed_*.parquet.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import polars as pl

from n8st.config import FINDINGS_DIR, NYC_TZ, PROCESSED_DIR, RAW_DIR

SUBWAYDATA = RAW_DIR / "mta_data" / "bulk" / "subwaydata"
# Days when weekday schedules didn't run (subway holiday service).
HOLIDAYS = {date(2026, 9, 7)}  # Labor Day


def load(folder: Path = SUBWAYDATA) -> pl.DataFrame:
    """One row per observed train stop."""
    trips = pl.read_parquet(folder / "*" / "trips.parquet", hive_partitioning=True)
    stops = pl.read_parquet(folder / "*" / "stop_times.parquet", hive_partitioning=True)
    trips = trips.select("trip_uid", "trip_id", "route_id", "date")
    df = stops.join(trips, on=["trip_uid", "date"], how="inner")

    def ts(col: str) -> pl.Expr:
        return (pl.from_epoch(pl.col(col).cast(pl.Int64), time_unit="s")
                .dt.replace_time_zone("UTC").dt.convert_time_zone(NYC_TZ))

    df = df.with_columns(
        arr=ts("arrival_time"), dep=ts("departure_time"),
        parent=pl.col("stop_id").str.slice(0, 3),
        direction=pl.col("stop_id").str.slice(3, 1),
    ).drop_nulls(["arr"])
    day = pl.col("arr").dt.date()
    return df.with_columns(
        service_day=day,
        hour=pl.col("arr").dt.hour(),
        daytype=pl.when(day.is_in(list(HOLIDAYS))).then(pl.lit("holiday"))
        .when(pl.col("arr").dt.weekday() <= 5).then(pl.lit("weekday"))
        .when(pl.col("arr").dt.weekday() == 6).then(pl.lit("saturday"))
        .otherwise(pl.lit("sunday")),
    ).select("date", "service_day", "daytype", "hour", "trip_uid", "route_id", "direction",
             "stop_id", "parent", "track", "arr", "dep")


def headways(df: pl.DataFrame, parent: str, direction: str, routes: list[str],
             max_gap_min: float = 30) -> pl.DataFrame:
    """Gaps between consecutive trains of any of `routes`, per service day."""
    return (
        df.filter((pl.col("parent") == parent) & (pl.col("direction") == direction)
                  & pl.col("route_id").is_in(routes))
        .unique(["trip_uid", "stop_id"])
        .sort("arr")
        .with_columns(gap_min=(pl.col("arr").diff().dt.total_seconds() / 60)
                      .over("service_day"))
        .filter(pl.col("gap_min").is_not_null() & (pl.col("gap_min") <= max_gap_min))
    )


def wait_table(hw: pl.DataFrame, hours: tuple[int, int] = (6, 24)) -> pl.DataFrame:
    """Per daytype and hour: trains/hour, median and 90th-percentile gap, expected wait.

    expected wait for a rider arriving at random = sum(h^2) / (2 sum(h)).
    """
    g = pl.col("gap_min")
    days = hw.group_by("daytype").agg(n_days=pl.col("service_day").n_unique())
    return (
        hw.filter(pl.col("hour").is_between(hours[0], hours[1] - 1))
        .group_by("daytype", "hour")
        .agg(trains=pl.len(), median_gap=g.median(), p90_gap=g.quantile(0.9),
             expected_wait=(g**2).sum() / (2 * g.sum()))
        .join(days, on="daytype")
        .with_columns(trains_per_hour=pl.col("trains") / pl.col("n_days"))
        .drop("trains")
        .sort("daytype", "hour")
    )


def segment_times(df: pl.DataFrame, route: str, a: str, b: str, direction: str) -> pl.DataFrame:
    """Observed seconds from departing parent a to arriving parent b, one row per trip.

    `stops_between` lists the parents served in between (so local and express runs
    can be told apart).
    """
    sub = df.filter((pl.col("route_id") == route) & (pl.col("direction") == direction))
    start = sub.filter(pl.col("parent") == a).select("trip_uid", "date", t0="dep")
    end = sub.filter(pl.col("parent") == b).select("trip_uid", "date", t1="arr")
    path = (sub.sort("arr").group_by("trip_uid", "date")
            .agg(pl.col("parent").alias("path"), pl.col("arr").alias("times")))
    seg = start.join(end, on=["trip_uid", "date"]).join(path, on=["trip_uid", "date"])
    seg = seg.with_columns(seconds=(pl.col("t1") - pl.col("t0")).dt.total_seconds()).filter(
        pl.col("seconds") > 0)
    seg = seg.with_columns(
        stops_between=pl.struct("path", "times", "t0", "t1").map_elements(
            lambda r: [p for p, t in zip(r["path"], r["times"], strict=True)
                       if r["t0"] < t < r["t1"]],
            return_dtype=pl.List(pl.String)),
        hour=pl.col("t0").dt.hour(),
        daytype=pl.when(pl.col("t0").dt.date().is_in(list(HOLIDAYS))).then(pl.lit("holiday"))
        .when(pl.col("t0").dt.weekday() <= 5).then(pl.lit("weekday"))
        .when(pl.col("t0").dt.weekday() == 6).then(pl.lit("saturday"))
        .otherwise(pl.lit("sunday")),
    )
    # Drop physically implausible runs (stale predictions collapse several stops).
    med = seg["seconds"].median()
    return seg.filter(pl.col("seconds") >= 0.5 * med)


def md(df: pl.DataFrame, digits: int = 1) -> str:
    df = df.with_columns(pl.col(pl.Float64, pl.Float32).round(digits))
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |"
              for r in df.iter_rows()]
    return "\n".join(lines)


def build_report(df: pl.DataFrame) -> tuple[str, dict[str, pl.DataFrame]]:
    span = f"{df['service_day'].min()} to {df['service_day'].max()}"
    n_days = df.group_by("daytype").agg(pl.col("service_day").n_unique()).sort("daytype")
    out = [
        "# Observed service on the Broadway line",
        "",
        f"subwaydata.nyc observed trips, {span}: "
        + ", ".join(f"{d} {n} days" for d, n in n_days.iter_rows()) + ".",
        "Times are the last real-time prediction before each train passed a stop "
        "(accurate to ~30 s).",
        "",
    ]
    tables: dict[str, pl.DataFrame] = {}

    # 1. The backtrack: downtown R/W at 14 St.
    hw = headways(df, "R20", "S", ["R", "W"])
    wt = wait_table(hw)
    tables["rw_14st_downtown"] = wt
    wk = wt.filter(pl.col("daytype") == "weekday").drop("daytype", "n_days")
    out += [
        "## 1. Your backtrack: downtown R/W at 14 St–Union Sq (weekdays)",
        "",
        "Gaps between consecutive downtown R or W trains, and the average wait for a rider "
        "who arrives at a random moment. Gaps over 30 min (service breaks) are excluded.",
        "",
        md(wk.select("hour", "trains_per_hour", "median_gap", "p90_gap", "expected_wait")),
        "",
    ]

    # 2. Cost of the local N: express weekday vs local weekend, observed.
    seg = segment_times(df, "N", "R17", "Q01", "S")
    seg = seg.with_columns(local=pl.col("stops_between").list.contains("R21"))
    st = (seg.filter(pl.col("hour").is_between(7, 21))
          .group_by("daytype", "local")
          .agg(trips=pl.len(), median_s=pl.col("seconds").median(),
               p25_s=pl.col("seconds").quantile(0.25), p75_s=pl.col("seconds").quantile(0.75),
               p90_s=pl.col("seconds").quantile(0.9))
          .sort("daytype", "local"))
    tables["n_34st_canal"] = st
    out += [
        "## 2. Downtown N, 34 St–Herald Sq to Canal St (bridge level), 7 am–9 pm",
        "",
        "`local = true` runs stopped at 8 St–NYU (the weekend pattern). The difference in "
        "medians is the observed cost of running the N local, per through-rider.",
        "",
        md(st, 0),
        "",
    ]
    try:
        express = st.filter((pl.col("daytype") == "weekday") & ~pl.col("local"))["median_s"][0]
        local = st.filter((pl.col("daytype") == "saturday") & pl.col("local"))["median_s"][0]
        out += [f"Observed local-minus-express: **{local - express:+.0f} s** "
                "(Saturday local vs weekday express medians).", ""]
    except IndexError:
        pass

    # 3. Your commute legs, observed in-train times, weekday 7-10 am.
    legs = [("D 71 St → W 4 St", "D", "B17", "D20", "N"),
            ("N 18 Av → 14 St", "N", "N05", "R20", "N"),
            ("N 18 Av → Canal", "N", "N05", "Q01", "N"),
            ("R/W 14 St → 8 St (backtrack ride)", "R", "R20", "R21", "S"),
            ("R Canal → 8 St", "R", "R23", "R21", "N")]
    rows = []
    for label, route, a, b, d in legs:
        s = segment_times(df, route, a, b, d).filter(
            (pl.col("daytype") == "weekday") & pl.col("hour").is_between(7, 9))
        if s.height:
            rows.append({"leg": label, "trips": s.height,
                         "median_min": s["seconds"].median() / 60,
                         "p90_min": s["seconds"].quantile(0.9) / 60})
    legs_df = pl.DataFrame(rows)
    tables["commute_legs"] = legs_df
    out += ["## 3. Your commute legs, observed in-train minutes (weekdays, 7–10 am departures)",
            "", md(legs_df), ""]

    # 4. Downtown D at 71 St and N at 18 Av: how long you wait at home.
    home = []
    for label, parent, routes in (("D at 71 St (toward Manhattan)", "B17", ["D"]),
                                  ("N at 18 Av (toward Manhattan)", "N05", ["N", "W"])):
        w = wait_table(headways(df, parent, "N", routes)).filter(
            (pl.col("daytype") == "weekday") & pl.col("hour").is_between(7, 9))
        home.append({"platform": label, "trains_per_hour": w["trains_per_hour"].mean(),
                     "median_gap": w["median_gap"].mean(),
                     "expected_wait": w["expected_wait"].mean()})
    home_df = pl.DataFrame(home)
    tables["home_waits"] = home_df
    out += ["## 4. Waiting at home, weekdays 7–10 am", "", md(home_df), ""]
    return "\n".join(out), tables


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", type=Path, default=SUBWAYDATA)
    args = parser.parse_args()
    df = load(args.dir)
    report, tables = build_report(df)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for name, t in tables.items():
        t.write_parquet(PROCESSED_DIR / f"observed_{name}.parquet")
    path = FINDINGS_DIR / "observed_service.md"
    path.write_text(report)
    print(report)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
