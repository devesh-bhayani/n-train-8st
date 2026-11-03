"""Turn logged shuttle positions into stop visits and headways.

A *visit* is a run of polls where one vehicle is within `radius_m` of a stop.
A new visit starts when the same vehicle has been away for more than
`max_gap_s`. Headway = time between consecutive visits by any vehicle on the
same route at the same stop. With 30 s polling, times are accurate to ~30 s.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from n8st.shuttle.passio import parse_stops

EARTH_RADIUS_M = 6_371_000
UNION_SQ = (40.735736, -73.990568)  # GTFS R20


def haversine_m(lat1: pl.Expr, lon1: pl.Expr, lat2: pl.Expr, lon2: pl.Expr) -> pl.Expr:
    rad = 3.141592653589793 / 180
    dlat = (lat2 - lat1) * rad
    dlon = (lon2 - lon1) * rad
    a = (dlat / 2).sin() ** 2 + (lat1 * rad).cos() * (lat2 * rad).cos() * (dlon / 2).sin() ** 2
    return 2 * EARTH_RADIUS_M * a.sqrt().arcsin()


def load_vehicles(shuttle_dir: Path) -> pl.DataFrame:
    return pl.read_parquet(shuttle_dir / "vehicles" / "**" / "*.parquet", hive_partitioning=True)


def load_stops(shuttle_dir: Path) -> pl.DataFrame:
    """Stops from the most recent metadata snapshot."""
    files = sorted((shuttle_dir / "meta").glob("date=*/stops-*.json"))
    if not files:
        raise FileNotFoundError(f"no stop snapshots under {shuttle_dir / 'meta'}")
    stops, _ = parse_stops(json.loads(files[-1].read_text()))
    return pl.DataFrame(stops)


def stops_near(stops: pl.DataFrame, point: tuple[float, float] = UNION_SQ,
               within_m: float = 500) -> pl.DataFrame:
    return stops.with_columns(
        dist_m=haversine_m(pl.lit(point[0]), pl.lit(point[1]),
                           pl.col("latitude"), pl.col("longitude"))
    ).filter(pl.col("dist_m") <= within_m).sort("dist_m")


def stop_visits(vehicles: pl.DataFrame, stops: pl.DataFrame, radius_m: float = 60,
                max_gap_s: float = 300) -> pl.DataFrame:
    near = (
        vehicles.select("polled_at", "vehicle_key", "route_id", "latitude", "longitude")
        .drop_nulls(["latitude", "longitude"])
        .join(stops.select("stop_id", "name", s_lat="latitude", s_lon="longitude"), how="cross")
        .with_columns(dist_m=haversine_m(pl.col("latitude"), pl.col("longitude"),
                                         pl.col("s_lat"), pl.col("s_lon")))
        .filter(pl.col("dist_m") <= radius_m)
        .sort("vehicle_key", "stop_id", "polled_at")
    )
    gap = pl.col("polled_at").diff().dt.total_seconds().over("vehicle_key", "stop_id")
    return (
        near.with_columns(new_visit=gap.is_null() | (gap > max_gap_s))
        .with_columns(visit_n=pl.col("new_visit").cum_sum().over("vehicle_key", "stop_id"))
        .group_by("vehicle_key", "stop_id", "name", "visit_n")
        .agg(
            route_id=pl.col("route_id").drop_nulls().first(),
            arrived=pl.col("polled_at").min(),
            departed=pl.col("polled_at").max(),
            closest_m=pl.col("dist_m").min(),
            polls=pl.len(),
        )
        .drop("visit_n")
        .sort("stop_id", "arrived")
    )


def headways(visits: pl.DataFrame) -> pl.DataFrame:
    return (
        visits.sort("route_id", "stop_id", "arrived")
        .with_columns(
            headway_min=pl.col("arrived").diff().dt.total_seconds().over("route_id", "stop_id")
            / 60
        )
    )


def headway_summary(hw: pl.DataFrame, tz: str = "America/New_York") -> pl.DataFrame:
    """Per route, stop and local hour: buses seen, median and worst gap, expected wait.

    expected_wait_min = sum(h^2) / (2 sum(h)), the average wait for a rider who
    turns up at a random time. Gaps longer than 90 min (service ended) are dropped.
    """
    h = pl.col("headway_min")
    return (
        hw.filter(h.is_not_null() & (h <= 90))
        .with_columns(hour=pl.col("arrived").dt.convert_time_zone(tz).dt.hour())
        .group_by("route_id", "stop_id", "name", "hour")
        .agg(
            buses=pl.len(),
            median_headway_min=h.median().round(1),
            max_headway_min=h.max().round(1),
            expected_wait_min=((h**2).sum() / (2 * h.sum())).round(1),
        )
        .sort("route_id", "stop_id", "hour")
    )
