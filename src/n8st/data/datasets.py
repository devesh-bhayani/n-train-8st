"""Download recipes for the MTA datasets this project uses.

    python -m n8st.data.datasets columns od_2025      # print a dataset's fields
    python -m n8st.data.datasets stations             # run this first
    python -m n8st.data.datasets ridership --edition 2025
    python -m n8st.data.datasets od --year 2025

Recipes filter on the server so you only download the stations this project needs.
Column names below come from the research notes and are checked before each pull.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from n8st.config import CAMPUS_AREA_STOPS, DATASETS, HOME_STOPS, RAW_DIR, SEA_BEACH_STOPS
from n8st.data import socrata

MTA_DIR = RAW_DIR / "mta"
STATIONS_PARQUET = MTA_DIR / "stations.parquet"


def stations() -> Path:
    socrata.require_columns(DATASETS["stations"], ["gtfs_stop_id", "complex_id"])
    return socrata.download(DATASETS["stations"], STATIONS_PARQUET)


def complex_ids(gtfs_stop_ids: list[str]) -> dict[str, str]:
    """Map GTFS parent-stop IDs to MTA station-complex IDs using the stations table."""
    if not STATIONS_PARQUET.exists():
        raise FileNotFoundError("Run `python -m n8st.data.datasets stations` first.")
    rows = duckdb.sql(
        f"SELECT CAST(gtfs_stop_id AS VARCHAR), CAST(complex_id AS VARCHAR) "
        f"FROM '{STATIONS_PARQUET}'"
    ).fetchall()
    lookup = dict(rows)
    missing = [s for s in gtfs_stop_ids if s not in lookup]
    if missing:
        raise KeyError(f"GTFS stops not found in stations table: {missing}")
    return {s: lookup[s] for s in gtfs_stop_ids}


def ridership(edition: str = "2025") -> Path:
    """Hourly entries at the campus-area and home stations."""
    dataset_id = DATASETS[f"hourly_ridership_{edition}"]
    socrata.require_columns(dataset_id, ["transit_timestamp", "station_complex_id", "ridership"])
    ids = sorted(set(complex_ids(CAMPUS_AREA_STOPS + HOME_STOPS).values()))
    return socrata.download(
        dataset_id,
        MTA_DIR / f"hourly_ridership_{edition}_focus.parquet",
        where=socrata.sql_in("station_complex_id", ids),
    )


def od(year: str = "2025") -> Path:
    """Origin-destination flows into the campus area, plus everything out of Sea Beach / home."""
    dataset_id = DATASETS[f"od_{year}"]
    socrata.require_columns(
        dataset_id,
        [
            "origin_station_complex_id",
            "destination_station_complex_id",
            "estimated_average_ridership",
        ],
    )
    campus = sorted(set(complex_ids(CAMPUS_AREA_STOPS).values()))
    home = sorted(set(complex_ids(HOME_STOPS + SEA_BEACH_STOPS).values()))
    where = (
        f"({socrata.sql_in('destination_station_complex_id', campus)}) OR "
        f"({socrata.sql_in('origin_station_complex_id', home)})"
    )
    return socrata.download(dataset_id, MTA_DIR / f"od_{year}_focus.parquet", where=where)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("columns")
    c.add_argument("name", choices=sorted(DATASETS))
    sub.add_parser("stations")
    r = sub.add_parser("ridership")
    r.add_argument("--edition", default="2025", choices=["2025", "2020_2024"])
    o = sub.add_parser("od")
    o.add_argument("--year", default="2025", choices=["2023", "2024", "2025", "2026"])
    args = parser.parse_args()

    if args.cmd == "columns":
        print("\n".join(socrata.columns(DATASETS[args.name])))
    elif args.cmd == "stations":
        print(f"saved {stations()}")
    elif args.cmd == "ridership":
        print(f"saved {ridership(args.edition)}")
    elif args.cmd == "od":
        print(f"saved {od(args.year)}")


if __name__ == "__main__":
    main()
