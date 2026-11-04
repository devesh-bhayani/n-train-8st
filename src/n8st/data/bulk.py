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
import tempfile
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

# Turnstile remote-unit IDs (stable across years; station *names* changed in late 2015).
# Broadway local stations, nearby controls, possible spillover, and other context stations.
TURNSTILE_UNITS = [
    "R082", "R083", "R085", "R086",  # 28 St, 23 St, 8 St-NYU, Prince St (Broadway)
    "R248", "R105", "R163", "R175", "R300", "R330", "R390", "R160", "R194", "R189", "R548",
    "R290", "R282", "R322",  # controls: 1 Av, 14 St (x3), 2 Av, 3 Av, 8 Av, Astor Pl,
    # Bleecker, Christopher (x2), Houston, Spring (x2)
    "R170", "R138",  # 14 St-Union Sq, W 4 St
    "R022", "R023", "R081", "R079", "R080", "R118", "R462", "R463", "R087", "R088", "R227",
    "R001", "R032", "R033", "R242", "R372", "R392", "R370",  # other Broadway + home stations
]
TURNSTILE_WINDOWS = {"turnstile_2015": ("2015-09-01", "2015-12-31"),
                     "turnstile_2016": ("2016-01-01", "2016-12-31"),
                     "turnstile_2017": ("2017-01-01", "2017-05-31")}

PERF_LINES = ["N", "Q", "R", "W", "B", "D", "F", "M"]
SUBWAYDATA_BASE = "https://data.subwaydata.nyc"
SUBWAYDATA_ROUTES = {"N", "Q", "R", "W", "B", "D", "F", "M"}
# Raw intermediate downloads live outside the output folder so they're never committed.
RAW_TMP = Path(tempfile.gettempdir()) / "n8st_raw"


# ---------------------------------------------------------------------------- helpers

def stations_table(out: Path) -> Path:
    """Stations lookup for filters. Kept outside `out` so parallel jobs don't commit copies."""
    path = Path(tempfile.gettempdir()) / "n8st_stations.parquet"
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
    return duckdb.sql(f"SELECT count(*) FROM '{path}'").fetchall()[0][0]


# ---------------------------------------------------------------------------- tasks

def task_stations(out: Path, _args) -> None:
    for name in ("stations", "complexes", "entrances"):
        p = socrata.download(DATASETS[name], out / "stations" / f"{name}.parquet")
        manifest(out, f"stations_{name}", {"dataset": DATASETS[name], "rows": rows_of(p)})


OD_COLUMNS = ("origin_station_complex_id, destination_station_complex_id, hour_of_day, "
              "day_of_week, estimated_average_ridership")


def task_od_matrix(out: Path, args) -> None:
    """Average-day hourly OD flows for one month, all station-complex pairs.

    Downloads the raw rows (five columns) and aggregates locally: server-side $group
    re-aggregates the whole month on every page (~6 min/page), raw pages take ~5 s.
    """
    year, month, daytype = args.year, args.month, args.daytype
    ds = DATASETS[f"od_{year}"]
    dows = DAYTYPES[daytype]
    raw = RAW_TMP / f"od_{year}_{month:02d}_{daytype}.parquet"
    socrata.download(ds, raw, select=OD_COLUMNS,
                     where=f"month = {month} AND {socrata.sql_in('day_of_week', dows)}",
                     page_size=args.page_size)
    path = out / "od" / f"od_{daytype}_{year}_{month:02d}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    # Sum the per-day-of-week averages, then divide by the number of days of week:
    # the average weekday (or Saturday, Sunday).
    duckdb.sql(f"""
        COPY (
            SELECT CAST(origin_station_complex_id AS SMALLINT) AS origin,
                   CAST(destination_station_complex_id AS SMALLINT) AS destination,
                   CAST(hour_of_day AS TINYINT) AS hour,
                   CAST(sum(estimated_average_ridership) / {len(dows)} AS FLOAT) AS riders
            FROM '{raw}'
            GROUP BY ALL
            HAVING sum(estimated_average_ridership) >= {args.min_sum}
            ORDER BY origin, destination, hour
        ) TO '{path}' (FORMAT parquet, COMPRESSION zstd)
    """)
    total = duckdb.sql(f"SELECT sum(riders) FROM '{path}'").fetchall()[0][0]
    manifest(out, path.stem, {"dataset": ds, "year": year, "month": month, "daytype": daytype,
                              "raw_rows": rows_of(raw), "rows": rows_of(path),
                              "riders_per_day": total, "min_sum_filter": args.min_sum})


def task_od_campus(out: Path, args) -> None:
    """Every flow into or out of the campus-area complexes, by month, day of week and hour."""
    year = args.year
    ds = DATASETS[f"od_{year}"]
    campus = complexes_for(out, CAMPUS_GTFS)
    raw = RAW_TMP / f"od_campus_{year}.parquet"
    socrata.download(ds, raw, select="month, " + OD_COLUMNS,
                     where=(f"{socrata.sql_in('destination_station_complex_id', campus)} OR "
                            f"{socrata.sql_in('origin_station_complex_id', campus)}"),
                     page_size=args.page_size)
    path = out / "od" / f"od_campus_{year}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    duckdb.sql(f"""
        COPY (
            SELECT CAST(month AS TINYINT) AS month, day_of_week,
                   CAST(hour_of_day AS TINYINT) AS hour,
                   CAST(origin_station_complex_id AS SMALLINT) AS origin,
                   CAST(destination_station_complex_id AS SMALLINT) AS destination,
                   CAST(sum(estimated_average_ridership) AS FLOAT) AS riders
            FROM '{raw}' GROUP BY ALL
        ) TO '{path}' (FORMAT parquet, COMPRESSION zstd)
    """)
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


def _months(start: str, end: str) -> list[tuple[str, str]]:
    """[(first day, first day of next month)] covering start..end."""
    d = date.fromisoformat(start).replace(day=1)
    stop = date.fromisoformat(end)
    out = []
    while d < stop:
        nxt = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
        out.append((d.isoformat(), min(nxt, stop).isoformat()))
        d = nxt
    return out


def _ridership_by_month(out: Path, args, name: str, select: str, group: str,
                        where_extra: str = "") -> None:
    """Aggregated ridership pulls, one month per query (the server aggregates fast when the
    filter is narrow), concatenated into one Parquet per edition."""
    for edition, lo, hi in _ridership_editions(args.start, args.end):
        parts = []
        for a, b in _months(lo, hi):
            p = RAW_TMP / f"{name}_{a[:7]}.parquet"
            socrata.download(
                DATASETS[edition], p, select=select, group=group, order=group,
                where=(f"transit_timestamp >= '{a}T00:00:00' AND "
                       f"transit_timestamp < '{b}T00:00:00'{where_extra}"),
                page_size=args.page_size)
            parts.append(p)
        path = out / "ridership" / f"{name}_{lo[:7]}_{hi[:7]}.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        files = ", ".join(f"'{p}'" for p in parts)
        duckdb.sql(f"COPY (SELECT * FROM read_parquet([{files}], union_by_name = true)) "
                   f"TO '{path}' (FORMAT parquet, COMPRESSION zstd)")
        manifest(out, path.stem, {"dataset": DATASETS[edition], "months": len(parts),
                                  "rows": rows_of(path)})


def task_ridership_hourly(out: Path, args) -> None:
    ids = complexes_for(out, FOCUS_GTFS)
    _ridership_by_month(
        out, args, "hourly_focus",
        select="transit_timestamp, station_complex_id, sum(ridership) AS entries, "
               "sum(transfers) AS transfers",
        group="transit_timestamp, station_complex_id",
        where_extra=f" AND {socrata.sql_in('station_complex_id', ids)}")


def task_ridership_daily(out: Path, args) -> None:
    _ridership_by_month(
        out, args, "daily_all",
        select="date_trunc_ymd(transit_timestamp) AS day, station_complex_id, "
               "sum(ridership) AS entries",
        group="date_trunc_ymd(transit_timestamp), station_complex_id")


def task_monthly(out: Path, args) -> None:
    path = socrata.download(DATASETS["monthly_station_ridership"],
                            out / "ridership" / "monthly_by_complex.parquet",
                            select="month, station_complex_id, station_complex, ridership, "
                                   "transfers")
    manifest(out, "monthly_by_complex", {"rows": rows_of(path)})


def task_turnstile(out: Path, args) -> None:
    units = socrata.sql_in("unit", TURNSTILE_UNITS)
    for name, (lo, hi) in TURNSTILE_WINDOWS.items():
        ds = DATASETS[name]
        # Station names and line codes as they appear, to check the filters.
        socrata.download(ds, out / "turnstile" / f"{name}_stations.parquet",
                         select="station, line_name, unit, count(*) AS n",
                         group="station, line_name, unit", order="station, line_name, unit")
        path = out / "turnstile" / f"{name}.parquet"
        socrata.download(
            ds, path,
            where=f"date >= '{lo}T00:00:00' AND date <= '{hi}T00:00:00' AND {units}",
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
            files = {m.name: tf.extractfile(m).read() for m in tf.getmembers() if m.isfile()}
        if not done:
            print("  archive members:", list(files), flush=True)
        trips_name = next(n for n in files if n.endswith("trips.csv"))
        stops_name = next(n for n in files if n.endswith("stop_times.csv"))
        trips = pl.read_csv(files[trips_name], infer_schema_length=0)
        stops = pl.read_csv(files[stops_name], infer_schema_length=0)
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


def task_probe_od(out: Path, args) -> None:
    """Time one page of the aggregated OD query (to size the full download)."""
    import time

    ds = DATASETS["od_2026"]
    keys = "origin_station_complex_id, destination_station_complex_id, hour_of_day"
    s = socrata._session()
    timings = {}
    for label, params in {
        "agg_month_weekday": {"$select": f"{keys}, sum(estimated_average_ridership) AS r",
                              "$where": f"month = 9 AND {socrata.sql_in('day_of_week', WEEKDAYS)}",
                              "$group": keys, "$order": keys, "$limit": 50000},
        "agg_month_weekday_hour8": {
            "$select": f"{keys}, sum(estimated_average_ridership) AS r",
            "$where": f"month = 9 AND hour_of_day = 8 AND "
                      f"{socrata.sql_in('day_of_week', WEEKDAYS)}",
            "$group": keys, "$order": keys, "$limit": 50000},
        "count_month_weekday": {"$select": "count(*) AS n",
                                "$where": f"month = 9 AND "
                                          f"{socrata.sql_in('day_of_week', WEEKDAYS)}"},
        "raw_page": {"$where": "month = 9", "$limit": 50000},
    }.items():
        t = time.monotonic()
        try:
            r = socrata._get(s, f"https://{socrata.SOCRATA_DOMAIN}/resource/{ds}.csv", params)
            timings[label] = {"seconds": round(time.monotonic() - t, 1),
                              "rows": len(r.content.splitlines()) - 1,
                              "head": r.text[:300]}
        except Exception as e:
            timings[label] = {"seconds": round(time.monotonic() - t, 1), "error": repr(e)[:300]}
        print(label, timings[label], flush=True)
    manifest(out, "probe_od", timings)


TASKS = {
    "probe-od": task_probe_od,
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
    for name in ("monthly", "turnstile", "perf", "probe-od"):
        sub.add_parser(name)
    args = p.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    TASKS[args.task](args.out, args)


if __name__ == "__main__":
    main()
