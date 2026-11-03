"""Poll NYU shuttle positions from Passio GO and append them to Parquet.

    n8st-shuttle-log --once                    # one poll, to check it works
    n8st-shuttle-log --duration-min 55         # what the GitHub Action runs each hour
    n8st-shuttle-log --duration-min 0          # run until Ctrl-C (laptop / Raspberry Pi)

Output, partitioned by New York service date:
    <out>/vehicles/date=YYYY-MM-DD/part-<run>-<n>.parquet   one row per vehicle per poll
    <out>/polls/date=YYYY-MM-DD/part-<run>-<n>.parquet      one row per poll (ok, latency, error)
    <out>/meta/date=YYYY-MM-DD/{routes,stops}-<run>.json    raw route and stop lists, once per run

The polls table makes gaps visible: a missing bus and a failed poll look the
same in the vehicles table, but not in the polls table.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl

from n8st.config import NYC_TZ, NYU_PASSIO_SYSTEM_ID, RAW_DIR
from n8st.shuttle.passio import PassioClient, now_utc, parse_vehicles

log = logging.getLogger("n8st.shuttle")
NY = ZoneInfo(NYC_TZ)
DEFAULT_OUT = RAW_DIR / "shuttle"

VEHICLE_SCHEMA = {
    "polled_at": pl.Datetime("us", "UTC"),
    "vehicle_key": pl.String,
    "bus_id": pl.String,
    "bus_name": pl.String,
    "bus_type": pl.String,
    "route_id": pl.String,
    "route_name": pl.String,
    "trip_id": pl.String,
    "latitude": pl.Float64,
    "longitude": pl.Float64,
    "speed": pl.Float64,
    "course": pl.Float64,
    "pax_load": pl.Float64,
    "capacity": pl.Float64,
    "route_block_id": pl.String,
    "out_of_service": pl.Boolean,
    "passio_created": pl.String,
    "color": pl.String,
    "extra": pl.String,
}
POLL_SCHEMA = {
    "polled_at": pl.Datetime("us", "UTC"),
    "ok": pl.Boolean,
    "n_vehicles": pl.Int32,
    "latency_ms": pl.Int32,
    "error": pl.String,
}


@dataclass
class RunStats:
    polls: int = 0
    ok: int = 0
    vehicle_rows: int = 0
    files: list[Path] = field(default_factory=list)


def service_date(ts: datetime) -> str:
    return ts.astimezone(NY).date().isoformat()


class Buffer:
    """Accumulates rows and writes them as date-partitioned Parquet parts."""

    def __init__(self, out_dir: Path, run_id: str):
        self.out_dir = out_dir
        self.run_id = run_id
        self.vehicles: list[dict] = []
        self.polls: list[dict] = []
        self.part = 0

    def flush(self) -> list[Path]:
        written = []
        for name, rows, schema in (
            ("vehicles", self.vehicles, VEHICLE_SCHEMA),
            ("polls", self.polls, POLL_SCHEMA),
        ):
            if not rows:
                continue
            df = pl.DataFrame(rows, schema=schema, orient="row")
            df = df.with_columns(
                _date=pl.col("polled_at").dt.convert_time_zone(NYC_TZ).dt.date().cast(pl.String)
            )
            for (day,), part in df.group_by("_date"):
                filename = f"part-{self.run_id}-{self.part:04d}.parquet"
                path = self.out_dir / name / f"date={day}" / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                part.drop("_date").write_parquet(path)
                written.append(path)
        self.vehicles, self.polls = [], []
        self.part += 1
        return written


def snapshot_meta(client: PassioClient, out_dir: Path, run_id: str, when: datetime) -> None:
    folder = out_dir / "meta" / f"date={service_date(when)}"
    folder.mkdir(parents=True, exist_ok=True)
    for name, fetch in (("routes", client.routes_raw), ("stops", client.stops_raw)):
        try:
            (folder / f"{name}-{run_id}.json").write_text(json.dumps(fetch(), sort_keys=True))
        except Exception as e:  # metadata is nice to have; never stop the run for it
            log.warning("could not fetch %s: %s", name, e)


def run(
    client: PassioClient,
    out_dir: Path = DEFAULT_OUT,
    interval_s: float = 30,
    duration_s: float | None = None,
    once: bool = False,
    flush_every: int = 20,
    clock: Callable[[], datetime] = now_utc,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> RunStats:
    started = clock()
    run_id = f"{started:%Y%m%dT%H%M%SZ}-{os.getpid()}"
    stats = RunStats()
    buffer = Buffer(out_dir, run_id)
    stop = {"flag": False}

    def _stop(signum, _frame):
        log.info("signal %s: finishing up", signum)
        stop["flag"] = True

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _stop)
        except ValueError:  # not in the main thread (e.g. tests)
            pass

    snapshot_meta(client, out_dir, run_id, started)
    t0 = monotonic()
    failures = 0
    while not stop["flag"]:
        polled_at = clock()
        tick = monotonic()
        try:
            raw = client.vehicles_raw()
            rows = parse_vehicles(raw, polled_at)
            buffer.vehicles.extend(rows)
            buffer.polls.append(
                {"polled_at": polled_at, "ok": True, "n_vehicles": len(rows),
                 "latency_ms": int((monotonic() - tick) * 1000), "error": None}
            )
            stats.ok += 1
            stats.vehicle_rows += len(rows)
            failures = 0
        except Exception as e:
            failures += 1
            log.warning("poll failed (%d in a row): %s", failures, e)
            buffer.polls.append(
                {"polled_at": polled_at, "ok": False, "n_vehicles": None,
                 "latency_ms": int((monotonic() - tick) * 1000), "error": str(e)[:500]}
            )
        stats.polls += 1

        if stats.polls % flush_every == 0:
            stats.files += buffer.flush()
        if once:
            break
        elapsed = monotonic() - t0
        if duration_s is not None and elapsed + interval_s >= duration_s:
            break
        # Back off after repeated failures, up to 8x the interval.
        wait = interval_s * min(2 ** max(failures - 1, 0), 8)
        # Keep to the schedule: subtract the time this poll took.
        sleep(max(0.0, wait - (monotonic() - tick)))

    stats.files += buffer.flush()
    log.info("done: %d polls, %d ok, %d vehicle rows", stats.polls, stats.ok, stats.vehicle_rows)
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--interval", type=float, default=30, help="seconds between polls")
    parser.add_argument("--duration-min", type=float, default=55,
                        help="stop after this many minutes; 0 = run until interrupted")
    parser.add_argument("--once", action="store_true", help="poll once and exit")
    parser.add_argument("--system-id", type=int, default=NYU_PASSIO_SYSTEM_ID)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    stats = run(
        PassioClient(system_id=args.system_id),
        out_dir=args.out,
        interval_s=args.interval,
        duration_s=None if args.duration_min == 0 else args.duration_min * 60,
        once=args.once,
    )
    print(f"polls={stats.polls} ok={stats.ok} vehicle_rows={stats.vehicle_rows} "
          f"files={len(stats.files)}")
    return 0 if stats.ok > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
