"""System-wide screen ("Start the Stop"): which express runs would be worth running local?

    python -m n8st.ledger.screen --od data/raw/mta_data/bulk/od/od_weekday_2026_04.parquet

Every express run found by n8st.scenarios.express_segments becomes a scenario: that
route makes the local stops on that stretch, timed with the local route's schedule.
The ledger then scores each one on the same OD data.

Phase averaging (see n8st.ledger.phase_avg): a run that slows route r also moves r's
trains relative to every route they share track or transfers with, and on one timetable
that alignment luck is worth +-1,000-2,600 rider-hours, as big as many real effects.
So for each offset in SCREEN_OFFSETS (centred on today's timetable), route r is
shifted by the same offset in the baseline and in every scenario on r, and the results
are averaged. Scenarios are grouped by route so each group shares its shifted baseline.

To keep ~80 scenarios x 4 offsets affordable, departures are sampled every 10 minutes
(6 am-11 pm, with jitter) and only three weight settings are used; the 8 St-NYU study
itself uses 3-minute sampling, ten offsets and the full grid.

This is a screen, not a verdict: track feasibility (crossovers at both ends), platform
lengths and capacity are not checked, and riders keep today's stations (fixed OD).
"""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path

import polars as pl

from n8st.config import FINDINGS_DIR, PROCESSED_DIR
from n8st.data import gtfs
from n8st.ledger import engine
from n8st.ledger.phase_check import shift_route
from n8st.ledger.run import STATIONS, complexes_from_stations, load_od
from n8st.routing import network
from n8st.scenarios import express_segments as es
from n8st.scenarios import make_local as ml

SCREEN_WEIGHTS = [engine.Weights(2.0, 2.0, 0.0), engine.BASE, engine.Weights(2.0, 2.0, 900.0)]
# Centred on today's timetable (see phase_avg): midpoints of [-12, +12) min, 6-min steps.
SCREEN_OFFSETS = [-540, -180, 180, 540]
BASE_COL = f"net_hours_{engine.BASE.label}"


def find_scenarios(feed: dict, limit: int = 0) -> tuple[list, dict]:
    """Every express run, plus what apply_run needs. Timetables are built later, one
    route at a time: holding all ~80 edited timetables at once takes ~7 GB."""
    raw = pl.read_parquet(STATIONS)
    ctx = {
        "complex_of": dict(raw.select("gtfs_stop_id", pl.col("complex_id").cast(pl.Float64)
                                      .cast(pl.Int64)).iter_rows()),
        "names": dict(raw.select("gtfs_stop_id", "stop_name").iter_rows()),
        "patterns": es.typical_patterns(feed),
        "medians": ml.segment_medians(feed),
    }
    coords = {g: (float(a), float(b)) for g, a, b in raw.select(
        "gtfs_stop_id", "gtfs_latitude", "gtfs_longitude").iter_rows()}
    runs = es.find_runs(ctx["patterns"], ctx["complex_of"], coords)
    return (runs[:limit] if limit else runs), ctx


def build_scenario(feed: dict, run, ctx: dict) -> tuple[dict | None, dict]:
    """(scenario feed or None if the local can't time it, description)."""
    f2, summ = ml.apply_run(feed, run, ctx["patterns"], ctx["complex_of"], ctx["medians"])
    names = ctx["names"]
    if summ.is_empty():
        return None, {}
    return f2, {"route": run.route, "direction": run.direction,
                "from": names.get(run.stops[0], run.stops[0]),
                "to": names.get(run.stops[-1], run.stops[-1]),
                "stops_added": len(run.inserted),
                "added_stations": ", ".join(names.get(s, s) for s in run.inserted),
                "trips": summ.height, "median_added_s": summ["added_s"].median()}


def run(od_path: Path, offsets: list[int], step_s: int, limit: int = 0,
        hours: range = range(6, 23)) -> tuple[pl.DataFrame, pl.DataFrame]:
    feed = gtfs.load(gtfs.GTFS_DIR / "subway_latest.zip")
    runs, ctx = find_scenarios(feed, limit)
    print(f"{len(runs)} express runs", flush=True)
    cidx = engine.complex_index(network.from_feed(feed, "Weekday"), complexes_from_stations())
    od = load_od(od_path)
    groups: dict[str, list] = defaultdict(list)
    for r in runs:
        groups[r.route].append(r)
    per_offset, info = [], {}
    for route, members in sorted(groups.items()):
        feeds = {}
        for r in members:
            f2, meta = build_scenario(feed, r, ctx)
            if f2 is not None:
                feeds[r.name], info[r.name] = f2, meta
        if not feeds:
            continue
        for d in offsets:
            t = time.monotonic()
            base = network.from_feed(shift_route(feed, route, d), "Weekday")
            nets = {n: network.from_feed(shift_route(f, route, d), "Weekday")
                    for n, f in feeds.items()}
            out = engine.run(base, nets, cidx, od, weights=SCREEN_WEIGHTS, hours=hours,
                             step_s=step_s, progress=False)
            per_offset.append(out["totals"].with_columns(offset_s=pl.lit(d)))
            print(f"  {route} offset {d:>4} s: {len(feeds)} scenarios in "
                  f"{time.monotonic() - t:.0f} s", flush=True)
            del base, nets, out
        del feeds
    allt = pl.concat(per_offset)
    meta = pl.DataFrame([{"scenario": k, **v} for k, v in info.items()])
    return allt, meta


def summarize(allt: pl.DataFrame, meta: pl.DataFrame, n_offsets: int) -> pl.DataFrame:
    avg = allt.group_by("scenario", "weights").agg(
        pl.col("net_hours").mean(), pl.col("net_hours").std().alias("sd"),
        pl.col("hours_saved").mean(), pl.col("hours_lost").mean(),
        pl.col("riders_affected").mean())
    wide = avg.pivot(on="weights", index="scenario", values="net_hours")
    wide.columns = ["scenario"] + [f"net_hours_{c}" for c in wide.columns[1:]]
    b = avg.filter(pl.col("weights") == engine.BASE.label).select(
        "scenario", "hours_saved", "hours_lost", "riders_affected",
        se=pl.col("sd") / n_offsets ** 0.5)
    return (meta.join(b, on="scenario").join(wide, on="scenario")
            .with_columns(net_per_added_stop=pl.col(BASE_COL) / pl.col("stops_added"),
                          clear=(pl.col(BASE_COL).abs() > 2 * pl.col("se")))
            .sort(BASE_COL))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--od", type=Path, required=True)
    p.add_argument("--step", type=int, default=600)
    p.add_argument("--offsets", type=int, nargs="*", default=SCREEN_OFFSETS)
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args()
    t_start = time.monotonic()
    allt, meta = run(args.od, args.offsets, args.step, args.limit)
    rank = summarize(allt, meta, len(args.offsets))
    tag = args.od.stem.replace("od_", "")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    allt.write_csv(PROCESSED_DIR / f"screen_express_runs_{tag}_per_offset.csv")
    rank.write_csv(PROCESSED_DIR / f"screen_express_runs_{tag}.csv")

    show = rank.select(
        "route", "direction", "from", "to", "stops_added", "median_added_s", "hours_saved",
        "hours_lost", pl.col(BASE_COL).alias("net_hours"), "se",
        pl.col(f"net_hours_{SCREEN_WEIGHTS[0].label}").alias("net_x0"),
        pl.col(f"net_hours_{SCREEN_WEIGHTS[2].label}").alias("net_x15"),
        "added_stations").with_columns(pl.col(pl.Float64).round(0))
    lines = ["| " + " | ".join(show.columns) + " |", "|" + "---|" * len(show.columns)]
    lines += ["| " + " | ".join("" if v is None else f"{v:,.0f}" if isinstance(v, float)
                                else str(v) for v in r) + " |"
              for r in show.iter_rows()]
    n_clear_good = rank.filter(pl.col("clear") & (pl.col(BASE_COL) < 0)).height
    n_clear_bad = rank.filter(pl.col("clear") & (pl.col(BASE_COL) > 0)).height
    text = "\n".join([
        "# System-wide screen: express runs made local",
        "",
        f"{rank.height} scenarios, OD `{args.od.name}`, departures every "
        f"{args.step // 60} min 6 am–11 pm with jitter, fixed stations. Each scenario's "
        f"route is shifted by {args.offsets} s in both baseline and scenario and the "
        "results averaged (phase averaging); `se` is the standard error of that average. "
        "`net_hours` uses base weights (2× wait/walk, 5-min transfer); `net_x0` and "
        "`net_x15` use 0- and 15-minute transfer penalties. Negative = riders save time. "
        "Sorted best first.",
        "",
        f"{n_clear_good} runs save time by more than two standard errors; {n_clear_bad} "
        f"cost time by more than two; the other {rank.height - n_clear_good - n_clear_bad} "
        "are within noise. Track feasibility is not checked: each row needs a track-map "
        "check (crossovers at both ends, platform lengths) before it means anything.",
        "",
        *lines,
        "",
        f"Runtime {round(time.monotonic() - t_start)} s.",
    ])
    (FINDINGS_DIR / f"screen_express_runs_{tag}.md").write_text(text)
    (PROCESSED_DIR / f"screen_meta_{tag}.json").write_text(json.dumps(
        {"od": str(args.od), "step_s": args.step, "offsets_s": args.offsets,
         "scenarios": rank.height, "runtime_s": round(time.monotonic() - t_start)}, indent=1))
    print(text)


if __name__ == "__main__":
    main()
