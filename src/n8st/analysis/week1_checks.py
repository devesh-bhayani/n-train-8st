"""Week-1 fact checks from the static GTFS schedule.

    python -m n8st.analysis.week1_checks [--gtfs data/raw/gtfs/subway_latest.zip]

Answers, from the published schedule (not observed trains):
  1. Which routes stop at 8 St-NYU on weekdays, Saturdays and Sundays?
  2. Do any W trips run on the Sea Beach line, giving a one-seat 18 Av -> 8 St ride?
  3. How often do R/W trains leave 8 St-NYU and 14 St, by hour? (scheduled headways)
  4. How much longer is the local N than the express N from 34 St to Canal St?

Writes docs/findings/week1_gtfs_checks.md.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import polars as pl

from n8st.config import (
    CANAL_BRIDGE,
    EIGHT_ST,
    FINDINGS_DIR,
    HERALD_SQ_BWAY,
    SEA_BEACH_STOPS,
    UNION_SQ_BWAY,
)
from n8st.data import gtfs

SERVICE_ORDER = ["Weekday", "Saturday", "Sunday"]


def hhmm(seconds: int | None) -> str:
    if seconds is None:
        return "-"
    seconds = int(seconds) % 86400
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}"


def time_band(seconds: pl.Expr) -> pl.Expr:
    hour = (seconds // 3600) % 24
    return (
        pl.when(hour < 6)
        .then(pl.lit("late night 00-06"))
        .when(hour < 21)
        .then(pl.lit("day 06-21"))
        .otherwise(pl.lit("evening 21-24"))
    )


def routes_serving(events: pl.DataFrame, stop: str) -> pl.DataFrame:
    """Trips per route, service day and time band that stop at a parent station."""
    return (
        events.filter(pl.col("parent_stop") == stop)
        .with_columns(band=time_band(pl.col("dep_s")))
        .group_by("route_id", "band", "service_id")
        .agg(trips=pl.col("trip_id").n_unique())
        .pivot(on="service_id", index=["route_id", "band"], values="trips")
        .sort("route_id", "band")
        .fill_null(0)
    )


def w_trips_on_sea_beach(events: pl.DataFrame) -> pl.DataFrame:
    """W trips that touch any Sea Beach station, with their times at 18 Av and 8 St."""
    w = events.filter(pl.col("route_id") == "W")
    sea_beach_trips = w.filter(pl.col("parent_stop").is_in(SEA_BEACH_STOPS))["trip_id"].unique()
    trips = w.filter(pl.col("trip_id").is_in(sea_beach_trips.implode()))
    return (
        trips.group_by("trip_id", "service_id", "direction")
        .agg(
            at_18_av=pl.col("dep_s").filter(pl.col("parent_stop") == "N05").first(),
            at_8_st=pl.col("dep_s").filter(pl.col("parent_stop") == EIGHT_ST).first(),
            via_montague=pl.col("parent_stop").is_in(["R28", "R27"]).any(),
            first_stop=pl.col("parent_stop").sort_by("stop_sequence").first(),
            last_stop=pl.col("parent_stop").sort_by("stop_sequence").last(),
        )
        .sort("service_id", "direction", "at_18_av")
    )


def headways(
    events: pl.DataFrame, stop: str, routes: list[str], service_id: str
) -> pl.DataFrame:
    """Scheduled departures per hour at a stop for a group of routes, by direction.

    expected_wait_min is the average wait for a rider who turns up at a random
    time: sum(h^2) / (2 * sum(h)). It equals half the headway only when trains
    are evenly spaced.
    """
    deps = (
        events.filter(
            (pl.col("parent_stop") == stop)
            & pl.col("route_id").is_in(routes)
            & (pl.col("service_id") == service_id)
        )
        .select("direction", "dep_s", "route_id")
        .sort("direction", "dep_s")
        .with_columns(headway_s=pl.col("dep_s").diff().over("direction"))
        .with_columns(hour=(pl.col("dep_s") // 3600) % 24)
    )
    return (
        deps.group_by("direction", "hour")
        .agg(
            trains=pl.len(),
            median_headway_min=(pl.col("headway_s").median() / 60).round(1),
            max_headway_min=(pl.col("headway_s").max() / 60).round(1),
            expected_wait_min=(
                (pl.col("headway_s") ** 2).sum() / (2 * pl.col("headway_s").sum()) / 60
            ).round(1),
        )
        .sort("direction", "hour")
    )


def run_times(
    events: pl.DataFrame, route: str, from_stop: str, to_stop: str, direction: str
) -> pl.DataFrame:
    """Scheduled running time between two stations, per service day and hour of departure."""
    ev = events.filter(
        (pl.col("route_id") == route)
        & (pl.col("direction") == direction)
        & pl.col("parent_stop").is_in([from_stop, to_stop])
    )
    a = ev.filter(pl.col("parent_stop") == from_stop).select("trip_id", "service_id", t0="dep_s")
    b = ev.filter(pl.col("parent_stop") == to_stop).select("trip_id", t1="arr_s")
    stops_between = events.filter(pl.col("route_id") == route).group_by("trip_id").agg(
        pl.col("parent_stop").sort_by("stop_sequence")
    )
    return (
        a.join(b, on="trip_id")
        .filter(pl.col("t1") > pl.col("t0"))
        .join(stops_between, on="trip_id")
        .with_columns(run_s=pl.col("t1") - pl.col("t0"), hour=(pl.col("t0") // 3600) % 24)
        .with_columns(
            stops_8st=pl.col("parent_stop").list.contains(EIGHT_ST),
        )
        .group_by("service_id", "hour", "stops_8st")
        .agg(trips=pl.len(), median_run_s=pl.col("run_s").median())
        .sort("service_id", "hour")
    )


def to_markdown(df: pl.DataFrame) -> str:
    cols = df.columns
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.iter_rows():
        lines.append("| " + " | ".join("" if v is None else str(v) for v in row) + " |")
    return "\n".join(lines)


def build_report(feed: dict[str, pl.DataFrame]) -> str:
    events = gtfs.stop_events(feed)
    cal = feed["calendar"]
    span = f"{cal['start_date'].min()} to {cal['end_date'].max()}"
    out = [
        "# Week-1 GTFS checks",
        "",
        f"Generated {date.today().isoformat()} from MTA static GTFS valid {span}. "
        "These are *scheduled* times; observed trains will differ.",
        "",
        "## 1. Routes stopping at 8 St-NYU (trips per day, both directions)",
        "",
        to_markdown(order_services(routes_serving(events, EIGHT_ST))),
        "",
    ]

    w = w_trips_on_sea_beach(events)
    out += ["## 2. W trips on the Sea Beach line", ""]
    if w.is_empty():
        out.append("No W trips touch a Sea Beach station in this feed.")
    else:
        summary = (
            w.group_by("service_id", "direction", "via_montague")
            .agg(
                trips=pl.len(),
                stop_18_av=pl.col("at_18_av").is_not_null().sum(),
                stop_8_st=pl.col("at_8_st").is_not_null().sum(),
                earliest_18_av=pl.col("at_18_av").min(),
                latest_18_av=pl.col("at_18_av").max(),
            )
            .with_columns(
                pl.col("earliest_18_av").map_elements(hhmm, return_dtype=pl.String),
                pl.col("latest_18_av").map_elements(hhmm, return_dtype=pl.String),
            )
        )
        out += [
            "Direction N = toward Manhattan. Times are departures from 18 Av.",
            "",
            to_markdown(summary),
            "",
            "Each trip:",
            "",
            to_markdown(
                w.with_columns(
                    pl.col("at_18_av").map_elements(hhmm, return_dtype=pl.String),
                    pl.col("at_8_st").map_elements(hhmm, return_dtype=pl.String),
                )
            ),
        ]
    out.append("")

    out += [
        "## 3. Scheduled R/W departures, weekdays",
        "",
        "Direction S = downtown. Your 14 St backtrack is a downtown R/W from 14 St (R20).",
        "",
        "### At 14 St-Union Sq (R20)",
        "",
        to_markdown(headways(events, UNION_SQ_BWAY, ["R", "W"], "Weekday")),
        "",
        "### At 8 St-NYU (R21)",
        "",
        to_markdown(headways(events, EIGHT_ST, ["R", "W"], "Weekday")),
        "",
    ]

    rt = run_times(events, "N", HERALD_SQ_BWAY, CANAL_BRIDGE, "S")
    pivot = (
        rt.filter(pl.col("hour").is_between(6, 22))
        .with_columns(pl.col("median_run_s").cast(pl.Int32))
        .pivot(on="service_id", index="hour", values="median_run_s")
        .sort("hour")
    )
    present = [s for s in SERVICE_ORDER if s in pivot.columns]
    pivot = pivot.select("hour", *present)
    if {"Weekday", "Saturday"} <= set(present):
        pivot = pivot.with_columns(
            local_penalty_s=pl.col("Saturday") - pl.col("Weekday"),
        )
    out += [
        "## 4. Downtown N, 34 St-Herald Sq (R17) to Canal St bridge level (Q01)",
        "",
        "Median scheduled seconds by hour of departure from 34 St. Weekday N runs express; "
        "weekend N runs local through 28 St, 23 St, 8 St and Prince St. "
        "`local_penalty_s` = Saturday minus Weekday: a first estimate of variant V1's cost "
        "per through-rider (weekend schedules carry different padding, so treat as rough).",
        "",
        to_markdown(pivot),
        "",
        "Trips by service day and whether they stop at 8 St:",
        "",
        to_markdown(
            rt.group_by("service_id", "stops_8st").agg(trips=pl.col("trips").sum()).sort(
                "service_id"
            )
        ),
        "",
    ]

    out += [
        "## 5. Your commute: scheduled in-train minutes, departures 7-10 am",
        "",
        "In-train time only; add walking, waiting and (for the N to 14 St) the backtrack.",
        "",
        to_markdown(commute_table(events)),
        "",
    ]
    return "\n".join(out)


COMMUTE_LEGS = [
    ("D 71 St -> W 4 St", "D", "B17", "D20"),
    ("N 18 Av -> 14 St (then backtrack)", "N", "N05", UNION_SQ_BWAY),
    ("N 18 Av -> 8 St (weekend local N)", "N", "N05", EIGHT_ST),
    ("W 18 Av -> 8 St (Sea Beach W trips)", "W", "N05", EIGHT_ST),
    ("R/W 14 St -> 8 St (the backtrack)", "R", UNION_SQ_BWAY, EIGHT_ST),
]


def commute_table(events: pl.DataFrame, hours: tuple[int, int] = (7, 9)) -> pl.DataFrame:
    rows = []
    for label, route, a, b in COMMUTE_LEGS:
        direction = "S" if b == EIGHT_ST and a == UNION_SQ_BWAY else "N"
        rt = run_times(events, route, a, b, direction).filter(pl.col("hour").is_between(*hours))
        for svc in SERVICE_ORDER:
            sub = rt.filter(pl.col("service_id") == svc)
            if sub.is_empty():
                continue
            minutes = (sub["median_run_s"] * sub["trips"]).sum() / sub["trips"].sum() / 60
            rows.append(
                {"leg": label, "service": svc, "trips": sub["trips"].sum(),
                 "in_train_min": round(minutes, 1)}
            )
    return pl.DataFrame(rows)


def order_services(df: pl.DataFrame) -> pl.DataFrame:
    keys = [c for c in df.columns if c not in SERVICE_ORDER]
    return df.select(*keys, *[s for s in SERVICE_ORDER if s in df.columns])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gtfs", type=Path, default=gtfs.GTFS_DIR / "subway_latest.zip")
    parser.add_argument("--out", type=Path, default=FINDINGS_DIR / "week1_gtfs_checks.md")
    args = parser.parse_args()
    report = build_report(gtfs.load(args.gtfs))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report)
    print(report)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
