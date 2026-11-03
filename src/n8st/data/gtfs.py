"""Download and load MTA static GTFS.

    python -m n8st.data.gtfs download [--feed subway|supplemented]

Each download is stored as data/raw/gtfs/<feed>_<feed_start_date>.zip so older
schedules are kept for before/after comparisons.
"""

from __future__ import annotations

import argparse
import io
import shutil
import zipfile
from pathlib import Path

import polars as pl
import requests

from n8st.config import GTFS_URLS, RAW_DIR, USER_AGENT

GTFS_DIR = RAW_DIR / "gtfs"
TABLES = ("stops", "routes", "trips", "stop_times", "calendar", "calendar_dates", "transfers")


def download(feed: str = "subway", dest_dir: Path = GTFS_DIR) -> Path:
    """Download a feed and save it under the feed's start date. Returns the zip path."""
    resp = requests.get(GTFS_URLS[feed], headers={"User-Agent": USER_AGENT}, timeout=120)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        calendar = pl.read_csv(zf.read("calendar.txt"), infer_schema=False)
    start = calendar["start_date"].min()
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"{feed}_{start}.zip"
    path.write_bytes(resp.content)
    shutil.copyfile(path, dest_dir / f"{feed}_latest.zip")
    return path


def time_to_seconds(col: pl.Expr) -> pl.Expr:
    """'25:13:30' -> 90810. GTFS times can pass 24:00 for trips after midnight."""
    parts = col.str.split(":")
    return (
        parts.list.get(0).cast(pl.Int32) * 3600
        + parts.list.get(1).cast(pl.Int32) * 60
        + parts.list.get(2).cast(pl.Int32)
    )


def load(path: Path | str = GTFS_DIR / "subway_latest.zip") -> dict[str, pl.DataFrame]:
    """Load the core tables as all-string frames, with stop times converted to seconds."""
    feed: dict[str, pl.DataFrame] = {}
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        for table in TABLES:
            if f"{table}.txt" in names:
                feed[table] = pl.read_csv(zf.read(f"{table}.txt"), infer_schema=False)
    st = feed["stop_times"]
    feed["stop_times"] = st.with_columns(
        arr_s=time_to_seconds(pl.col("arrival_time")),
        dep_s=time_to_seconds(pl.col("departure_time")),
        stop_sequence=pl.col("stop_sequence").cast(pl.Int32),
        parent_stop=pl.col("stop_id").str.replace(r"[NS]$", ""),
        direction=pl.col("stop_id").str.slice(-1),
    )
    return feed


def stop_events(feed: dict[str, pl.DataFrame]) -> pl.DataFrame:
    """Every scheduled train stop, joined to its route and service day."""
    trips = feed["trips"].select("trip_id", "route_id", "service_id")
    return feed["stop_times"].join(trips, on="trip_id", how="inner")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    dl = sub.add_parser("download")
    dl.add_argument("--feed", choices=sorted(GTFS_URLS), default="subway")
    args = parser.parse_args()
    if args.cmd == "download":
        print(f"saved {download(args.feed)}")


if __name__ == "__main__":
    main()
