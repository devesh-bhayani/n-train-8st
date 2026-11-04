"""System-wide screen ("Start the Stop"): which express runs would be worth running local?

    python -m n8st.ledger.screen --od data/raw/mta_data/bulk/od/od_weekday_2026_04.parquet

Every express run found by n8st.scenarios.express_segments becomes a scenario: that
route makes the local stops on that stretch, timed with the local route's schedule.
The ledger then scores each one on the same OD data. To keep 78 scenarios affordable,
departures are sampled every 10 minutes (6 am-11 pm) and only three weight settings
are used; the 8 St-NYU study itself uses 2-minute sampling and the full grid.

This is a screen, not a verdict: track feasibility (crossovers at both ends), platform
lengths and capacity are not checked, and riders keep today's stations (fixed OD).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import polars as pl

from n8st.config import FINDINGS_DIR, PROCESSED_DIR
from n8st.data import gtfs
from n8st.ledger import engine
from n8st.ledger.run import STATIONS, complexes_from_stations, load_od
from n8st.routing import network
from n8st.scenarios import express_segments as es
from n8st.scenarios import make_local as ml

SCREEN_WEIGHTS = [engine.Weights(2.0, 2.0, 0.0), engine.BASE, engine.Weights(2.0, 2.0, 900.0)]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--od", type=Path, required=True)
    p.add_argument("--step", type=int, default=600)
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args()
    t_start = time.monotonic()

    feed = gtfs.load(gtfs.GTFS_DIR / "subway_latest.zip")
    raw = pl.read_parquet(STATIONS)
    complex_of = dict(raw.select("gtfs_stop_id", pl.col("complex_id").cast(pl.Float64)
                                 .cast(pl.Int64)).iter_rows())
    coords = {g: (float(a), float(b)) for g, a, b in raw.select(
        "gtfs_stop_id", "gtfs_latitude", "gtfs_longitude").iter_rows()}
    names = dict(raw.select("gtfs_stop_id", "stop_name").iter_rows())
    patterns = es.typical_patterns(feed)
    runs = es.find_runs(patterns, complex_of, coords)
    if args.limit:
        runs = runs[: args.limit]
    medians = ml.segment_medians(feed)

    base = network.from_feed(feed, "Weekday")
    nets, info = {}, {}
    for run in runs:
        f2, summ = ml.apply_run(feed, run, patterns, complex_of, medians)
        if summ.is_empty():
            continue
        nets[run.name] = network.from_feed(f2, "Weekday")
        info[run.name] = {"route": run.route, "direction": run.direction,
                          "from": names.get(run.stops[0], run.stops[0]),
                          "to": names.get(run.stops[-1], run.stops[-1]),
                          "stops_added": len(run.inserted),
                          "added_stations": ", ".join(names.get(s, s) for s in run.inserted),
                          "trips": summ.height, "median_added_s": summ["added_s"].median()}
    print(f"{len(nets)} scenarios built", flush=True)

    cidx = engine.complex_index(base, complexes_from_stations())
    od = load_od(args.od)
    out = engine.run(base, nets, cidx, od, weights=SCREEN_WEIGHTS, hours=range(6, 23),
                     step_s=args.step)
    t = out["totals"].pivot(on="weights", index="scenario", values="net_hours")
    t.columns = ["scenario"] + [f"net_hours_{c}" for c in t.columns[1:]]
    b = out["totals"].filter(pl.col("weights") == engine.BASE.label).select(
        "scenario", "hours_saved", "hours_lost", "riders_affected")
    meta = pl.DataFrame([{"scenario": k, **v} for k, v in info.items()])
    rank = (meta.join(b, on="scenario").join(t, on="scenario")
            .with_columns(net_per_added_stop=pl.col(f"net_hours_{engine.BASE.label}")
                          / pl.col("stops_added"))
            .sort(f"net_hours_{engine.BASE.label}"))
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    rank.write_csv(PROCESSED_DIR / "screen_express_runs.csv")

    show = rank.select("route", "direction", "from", "to", "stops_added", "median_added_s",
                       "hours_saved", "hours_lost", f"net_hours_{engine.BASE.label}",
                       "added_stations").with_columns(
        pl.col(pl.Float64).round(0))
    lines = ["| " + " | ".join(show.columns) + " |", "|" + "---|" * len(show.columns)]
    lines += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |"
              for r in show.iter_rows()]
    text = "\n".join([
        "# System-wide screen: express runs made local",
        "",
        f"{len(nets)} scenarios, OD `{args.od.name}`, departures every {args.step // 60} min "
        "6 am–11 pm, fixed stations, base weights (2× wait/walk, 5-min transfer). "
        "Negative net = riders save time. Sorted best first. Track feasibility is not "
        "checked: each row needs a track-map check before it means anything.",
        "",
        *lines,
        "",
        f"Runtime {round(time.monotonic() - t_start)} s.",
    ])
    (FINDINGS_DIR / "screen_express_runs.md").write_text(text)
    (PROCESSED_DIR / "screen_meta.json").write_text(json.dumps(
        {"od": str(args.od), "step_s": args.step, "scenarios": len(nets)}, indent=1))
    print(text)


if __name__ == "__main__":
    main()
