"""Bulk downloads, run on GitHub Actions (see .github/workflows/fetch-data.yml).

    python -m n8st.data.bulk --out _out/bulk stations
    python -m n8st.data.bulk --out _out/bulk od-matrix 2026 9            # weekday hourly OD
    python -m n8st.data.bulk --out _out/bulk od-matrix 2026 9 --daytype saturday
    python -m n8st.data.bulk --out _out/bulk od-campus 2025              # all flows to/from campus
    python -m n8st.data.bulk --out _out/bulk ridership-hourly 2022-02-01 2026-11-01
    python -m n8st.data.bulk --out _out/bulk ridership-daily 2022-02-01 2026-11-01
    python -m n8st.data.bulk --out _out/bulk monthly
    python -m n8st.data.bulk --out _out/bulk turnstile
    python -m n8st.data.bulk --out _out/bulk perf
    python -m n8st.data.bulk --out _out/bulk subwaydata 2026-09-02 2026-11-02

Aggregation happens on the server (SoQL $group) to keep files small enough for git.
Column names and encodings were verified by the recon run of 2026-11-04.
"""

from __future__ import annotations

import argparse
import io
import json
import lzma
import tarfile
from datetime import date, timedelta
from pathlib import Path

import duckdb
import polars as pl
import requests

from n8st.config import DATASETS, SEA_BEACH_STOPS, USER_AGENT, WEEKDAYS
from n8st.data import socrata

CAMPUS_GTFS = ["R21", "R22", "R20", "D20", "636", "R23", "Q01", "D21"]
BROADWAY_GTFS = [f"R{n}" for n in range(13, 32)] + ["Q01"]
WEST_END_GTFS = [f"B{n}" for n in range(12, 24)]
NEARBY_GTFS = ["D20", "636", "D21", "133", "638", "A33", "A34", "639", "L03", "635", "R20",
               "A32", "D19", "L02", "132"]
FOCUS_GTFS = sorted(set(BROADWAY_GTFS + SEA_BEACH_STOPS + WEST_END_GTFS + NEARBY_GTFS))

DAYTYPES = {"weekday": WEEKDAYS, "saturday": ("Saturday",), "sunday": ("Sunday",)}

TURNSTILE_TREATED = ["8 ST-NYU", "PRINCE ST", "23 ST", "28 ST", "14 ST-UNION SQ", "CANAL ST",
                     "34 ST-HERALD SQ", "49 ST", "57 ST-7 AV", "5 AV/59 ST", "CITY HALL",
                     "CORTLANDT ST", "RECTOR ST", "WHITEHALL S-FRY", "TIMES SQ-42 ST"]
TURNSTILE_CONTROLS = ["ASTOR PL", "BLEECKER ST", "W 4 ST-WASH SQ", "CHRISTOPHER ST",
                      "SPRING ST", "HOUSTON ST", "BROADWAY/LAFAY", "2 AV", "1 AV", "3 AV",
                      "14 ST", "6 AV", "8 AV", "18 AV", "71 ST"]
TURNSTILE_WINDOWS = {"turnstile_2015": ("2015-09-01", "2015-12-31"),
                     "turnstile_2016": ("2016-01-01", "2016-12-31"),
                     "turnstile_2017": ("2017-01-01", "2017-05-31")}

PERF_LINES = ["N", "Q", "R", "W", "B", "D", "F", "M"]
SUBWAYDATA_BASE = "https://data.subwaydata.nyc"
SUBWAYDATA_ROUTES = {"N", "Q", "R", "W", "B", "D", "F", "M"}


# ---------------------------------------------------------------------------- helpers

def stations_table(out: Path) -> Path:
    path = out / "stations" / "stations.parquet"
    if not path.exists():
        socrata.download(DATASETS["stations"], path)
    return path


def complexes_for(out: Path, gtfs_ids: list[str]) -> list[str]:
    path = stations_table(out)
    rows = duckdb.sql(
        f"SELECT DISTINCT CAST(complex_id AS VARCHAR) FROM '{path}' "
        f"WHERE gtfs_stop_id IN ({', '.join(repr(g) for g in gtfs_ids)})"
    ).fetchall()
    return sorted({r[0] for r in rows})


def manifest(out: Path, name: str, info: dict) -> None:
    path = out / "manifest" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(info, indent=1, default=str))


def rows_of(path: Path) -> int:
    return duckdb.sql(f"SELECT count(*) FROM '{path}'").fetchone()[0]


# ---------------------------------------------------------------------------- tasks

def task_stations(out: Path, _args) -> None:
    for name in ("stations", "complexes", "entrances"):
        p = socrata.download(DATASETS[name], out / "stations" / f"{name}.parquet")
        manifest(out, f"stations_{name}", {"dataset": DATASETS[name], "rows": rows_of(p)})


def task_od_matrix(out: Path, args) -> None:
    """Average-day hourly OD flows for one month, all station-complex pairs."""
    year, month, daytype = args.year, args.month, args.daytype
    ds = DATASETS[f"od_{year}"]
    dows = DAYTYPES[daytype]
    keys = "origin_station_complex_id, destination_station_complex_id, hour_of_day"
    path = out / "od" / f"od_{daytype}_{year}_{month:02d}.parquet"
    socrata.download(
        ds, path,
        select=f"{keys}, sum(estimated_average_ridership) AS riders_sum",
        where=f"month = {month} AND {socrata.sql_in('day_of_week', dows)}",
        group=keys,
        having=f"sum(estimated_average_ridership) >= {args.min_sum}",
        order=keys,
        page_size=args.page_size,
    )
    # riders_sum adds the per-day-of-week averages; divide by the number of days of week.
    tmp = path.with_suffix(".tmp.parquet")
    duckdb.sql(f"""
        COPY (
            SELECT CAST(origin_station_complex_id AS SMALLINT) AS origin,
                   CAST(destination_station_complex_id AS SMALLINT) AS destination,
                   CAST(hour_of_day AS TINYINT) AS hour,
                   CAST(riders_sum / {len(dows)} AS FLOAT) AS riders
            FROM '{path}'
        ) TO '{tmp}' (FORMAT parquet, COMPRESSION zstd)
    """)
    tmp.replace(path)
    total = duckdb.sql(f"SELECT sum(riders) FROM '{path}'").fetchone()[0]
    manifest(out, path.stem, {"dataset": ds, "year": year, "month": month, "daytype": daytype,
                              "rows": rows_of(path), "riders_per_day": total,
                              "min_sum_filter": args.min_sum})


def task_od_campus(out: Path, args) -> None:
    """Every flow into or out of the campus-area complexes, by month, day of week and hour."""
    year = args.year
    ds = DATASETS[f"od_{year}"]
    campus = complexes_for(out, CAMPUS_GTFS)
    keys = ("month, day_of_week, hour_of_day, origin_station_complex_id, "
            "destination_station_complex_id")
    path = out / "od" / f"od_campus_{year}.parquet"
    socrata.download(
        ds, path,
        select=f"{keys}, sum(estimated_average_ridership) AS riders",
        where=(f"{socrata.sql_in('destination_station_complex_id', campus)} OR "
               f"{socrata.sql_in('origin_station_complex_id', campus)}"),
        group=keys, having="sum(estimated_average_ridership) >= 0.05", order=keys,
        page_size=args.page_size,
    )
    manifest(out, path.stem, {"dataset": ds, "campus_complexes": campus, "rows": rows_of(path)})


def _ridership_editions(start: str, end: str) -> list[tuple[str, str, str]]:
    eds = [("hourly_ridership_2017_2019", "2017-01-01", "2020-01-01"),
           ("hourly_ridership_2020_2024", "2020-01-01", "2025-01-01"),
           ("hourly_ridership_2025", "2025-01-01", "2100-01-01")]
    out = []
    for name, a, b in eds:
        lo, hi = max(a, start), min(b, end)
        if lo < hi:
            out.append((name, lo, hi))
    return out


def task_ridership_hourly(out: Path, args) -> None:
    ids = complexes_for(out, FOCUS_GTFS)
    for name, lo, hi in _ridership_editions(args.start, args.end):
        path = out / "ridership" / f"hourly_focus_{lo[:7]}_{hi[:7]}.parquet"
        socrata.download(
            DATASETS[name], path,
            select="transit_timestamp, station_complex_id, sum(ridership) AS entries, "
                   "sum(transfers) AS transfers",
            where=(f"transit_timestamp >= '{lo}T00:00:00' AND transit_timestamp < '{hi}T00:00:00'"
                   f" AND {socrata.sql_in('station_complex_id', ids)}"),
            group="transit_timestamp, station_complex_id",
            order="transit_timestamp, station_complex_id", page_size=args.page_size,
        )
        manifest(out, path.stem, {"dataset": DATASETS[name], "complexes": ids,
                                  "rows": rows_of(path)})


def task_ridership_daily(out: Path, args) -> None:
    for name, lo, hi in _ridership_editions(args.start, args.end):
        path = out / "ridership" / f"daily_all_{lo[:7]}_{hi[:7]}.parquet"
        socrata.download(
            DATASETS[name], path,
            select="date_trunc_ymd(transit_timestamp) AS day, station_complex_id, "
                   "sum(ridership) AS entries",
            where=f"transit_timestamp >= '{lo}T00:00:00' AND transit_timestamp < '{hi}T00:00:00'",
            group="date_trunc_ymd(transit_timestamp), station_complex_id",
            order="date_trunc_ymd(transit_timestamp), station_complex_id",
            page_size=args.page_size,
        )
        manifest(out, path.stem, {"dataset": DATASETS[name], "rows": rows_of(path)})


def task_monthly(out: Path, args) -> None:
    path = socrata.download(DATASETS["monthly_station_ridership"],
                            out / "ridership" / "monthly_by_complex.parquet",
                            select="month, station_complex_id, station_complex, ridership, "
                                   "transfers")
    manifest(out, "monthly_by_complex", {"rows": rows_of(path)})


def task_turnstile(out: Path, args) -> None:
    names = socrata.sql_in("station", TURNSTILE_TREATED)
    controls = socrata.sql_in("station", TURNSTILE_CONTROLS)
    for name, (lo, hi) in TURNSTILE_WINDOWS.items():
        ds = DATASETS[name]
        # Station names and line codes as they appear, to check the filters.
        socrata.download(ds, out / "turnstile" / f"{name}_stations.parquet",
                         select="station, line_name, unit, count(*) AS n",
                         group="station, line_name, unit", order="station, line_name, unit")
        path = out / "turnstile" / f"{name}.parquet"
        socrata.download(
            ds, path,
            where=(f"date >= '{lo}T00:00:00' AND date <= '{hi}T00:00:00' AND "
                   f"(({names} AND line_name LIKE '%R%') OR {controls})"),
            page_size=args.page_size,
        )
        manifest(out, name, {"dataset": ds, "window": [lo, hi], "rows": rows_of(path)})


def task_perf(out: Path, args) -> None:
    lines = socrata.sql_in("line", PERF_LINES)
    for name, where in (("cjm_2015_2019", None), ("wait_assessment", None),
                        ("service_delivered", None), ("end_to_end_runtimes", lines),
                        ("subway_paths", lines)):
        path = socrata.download(DATASETS[name], out / "perf" / f"{name}.parquet", where=where)
        manifest(out, f"perf_{name}", {"dataset": DATASETS[name], "rows": rows_of(path)})


def task_subwaydata(out: Path, args) -> None:
    """Observed trips (every train's actual stop times) from subwaydata.nyc, filtered."""
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    meta = s.get(f"{SUBWAYDATA_BASE}/subwaydatanyc_metadata.json", timeout=120).json()
    by_day = {d["Day"]: d for d in meta["ProcessedDays"]}
    day = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    done, missing = [], []
    while day <= end:
        key = day.isoformat()
        entry = by_day.get(key)
        day += timedelta(days=1)
        if not entry:
            missing.append(key)
            continue
        r = s.get(f"{SUBWAYDATA_BASE}/{entry['Csv']['Path']}", timeout=300)
        r.raise_for_status()
        with tarfile.open(fileobj=io.BytesIO(lzma.decompress(r.content))) as tf:
            files = {m.name.split("/")[-1]: tf.extractfile(m).read()
                     for m in tf.getmembers() if m.isfile()}
        trips = pl.read_csv(files["trips.csv"], infer_schema_length=0)
        stops = pl.read_csv(files["stop_times.csv"], infer_schema_length=0)
        route_col = next(c for c in trips.columns if c.startswith("route"))
        key_col = next(c for c in trips.columns if c in stops.columns)
        trips = trips.filter(pl.col(route_col).is_in(list(SUBWAYDATA_ROUTES)))
        stops = stops.join(trips.select(key_col), on=key_col, how="semi")
        folder = out / "subwaydata" / f"date={key}"
        folder.mkdir(parents=True, exist_ok=True)
        trips.write_parquet(folder / "trips.parquet", compression="zstd")
        stops.write_parquet(folder / "stop_times.parquet", compression="zstd")
        done.append({"day": key, "trips": trips.height, "stop_times": stops.height,
                     "trip_columns": trips.columns, "stop_columns": stops.columns})
        print(f"  subwaydata {key}: {trips.height} trips, {stops.height} stop times", flush=True)
    manifest(out, f"subwaydata_{args.start}_{args.end}", {"days": done, "missing": missing})


TASKS = {
    "stations": task_stations,
    "od-matrix": task_od_matrix,
    "od-campus": task_od_campus,
    "ridership-hourly": task_ridership_hourly,
    "ridership-daily": task_ridership_daily,
    "monthly": task_monthly,
    "turnstile": task_turnstile,
    "perf": task_perf,
    "subwaydata": task_subwaydata,
}


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--page-size", type=int, default=50_000)
    sub = p.add_subparsers(dest="task", required=True)
    sub.add_parser("stations")
    m = sub.add_parser("od-matrix")
    m.add_argument("year")
    m.add_argument("month", type=int)
    m.add_argument("--daytype", choices=sorted(DAYTYPES), default="weekday")
    m.add_argument("--min-sum", type=float, default=0.25,
                   help="drop pair-hours whose summed daily averages are below this")
    c = sub.add_parser("od-campus")
    c.add_argument("year")
    for name in ("ridership-hourly", "ridership-daily", "subwaydata"):
        r = sub.add_parser(name)
        r.add_argument("start")
        r.add_argument("end")
    for name in ("monthly", "turnstile", "perf"):
        sub.add_parser(name)
    args = p.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    TASKS[args.task](args.out, args)


if __name__ == "__main__":
    main()
