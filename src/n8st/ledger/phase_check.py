"""How sensitive is the ledger to timetable phase, i.e. *when* trains run relative to
each other, as opposed to how long they take?

Shifting every weekday N trip by a few seconds changes no running time, yet it changes
how N trains interleave with the Q and R/W at shared stations, and therefore waits.
If that alone moves the ledger by hundreds of hours, scenario results must be averaged
over phases instead of read off one arbitrary alignment.

    python -m n8st.ledger.phase_check --od data/raw/mta_data/bulk/od/od_weekday_2026_04.parquet
"""

from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl

from n8st.config import FINDINGS_DIR
from n8st.data import gtfs
from n8st.ledger import engine
from n8st.ledger.run import complexes_from_stations, load_od
from n8st.routing import network


def shift_route(feed: dict, route: str, seconds: int, service_id: str = "Weekday") -> dict:
    ids = feed["trips"].filter((pl.col("route_id") == route)
                               & (pl.col("service_id") == service_id))["trip_id"].to_list()
    st = feed["stop_times"].with_columns(
        arr_s=pl.when(pl.col("trip_id").is_in(ids)).then(pl.col("arr_s") + seconds)
        .otherwise(pl.col("arr_s")),
        dep_s=pl.when(pl.col("trip_id").is_in(ids)).then(pl.col("dep_s") + seconds)
        .otherwise(pl.col("dep_s")))
    f2 = dict(feed)
    f2["stop_times"] = st
    return f2


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--od", type=Path, required=True)
    p.add_argument("--shifts", type=int, nargs="*", default=[20, 60, 120, 240])
    args = p.parse_args()
    feed = gtfs.load(gtfs.GTFS_DIR / "subway_latest.zip")
    base = network.from_feed(feed, "Weekday")
    nets = {f"N_shift_{s}s": network.from_feed(shift_route(feed, "N", s), "Weekday")
            for s in args.shifts}
    cidx = engine.complex_index(base, complexes_from_stations())
    od = load_od(args.od)
    out = engine.run(base, nets, cidx, od, weights=[engine.BASE], hours=range(6, 23),
                     step_s=300)
    t = out["totals"].select("scenario", "net_hours", "hours_saved", "hours_lost")
    lines = ["| " + " | ".join(t.columns) + " |", "|" + "---|" * len(t.columns)]
    lines += ["| " + " | ".join(f"{v:,.0f}" if isinstance(v, float) else str(v) for v in r)
              + " |" for r in t.iter_rows()]
    text = "\n".join([
        "# Timetable phase sensitivity",
        "",
        "Every weekday N trip shifted later by a fixed number of seconds, nothing else "
        "changed (no running time, no stops). Base weights, 6 am–11 pm, 5-minute sampling.",
        "",
        *lines,
        "",
    ])
    (FINDINGS_DIR / "phase_sensitivity.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
