"""Phase-averaged ledger: separate the cost of a stop pattern from timetable luck.

The MTA timetables the N so it interleaves with the W (Astoria), the Q (Broadway, the
Manhattan Bridge, Brighton) and the R/D (4th Av). A scenario that delays N trains after
the new stops also moves them relative to those routes, and that misalignment costs
riders waiting time even though a real timetable would be re-planned to avoid it.
(docs/findings/phase_sensitivity.md: shifting every N trip by 20-240 s, with nothing
else changed, "costs" 1,000-5,500 rider-hours.)

So: for each offset delta in a window covering the N's headway, shift *all* N trips by
delta in both the baseline and the scenario, run the ledger, and average. Whatever
coordination quality the N has is then the same, on average, with and without the
change, and the difference is the effect of the stopping pattern itself.

The window matters. A scenario that delays the N by D seconds downstream averages its
downstream phases over [D, W + D) while the baseline averages over [0, W). If W were
exactly one headway the two sets would be the same mod the headway and the bias would
vanish; the N's headway varies through the day, so instead the window is made wide
(0-18 min, about two midday headways), which shrinks the leftover end effect to roughly
D / W of the spread in coordination quality. The pure-shift check measures what is left.

    python -m n8st.ledger.phase_avg --od data/raw/mta_data/bulk/od/od_weekday_2026_04.parquet
    python -m n8st.ledger.phase_avg --check   # pure shifts should average to ~0
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import polars as pl

from n8st.config import FINDINGS_DIR, PROCESSED_DIR
from n8st.data import gtfs
from n8st.ledger import engine, flex
from n8st.ledger.phase_check import shift_route
from n8st.ledger.run import STATIONS, VARIANTS, complexes_from_stations, load_od
from n8st.routing import network
from n8st.scenarios import timetable as tt

# 0-18 min in 2-min steps. The N runs every ~8-10 min by day and 12-20 min late evening.
DEFAULT_OFFSETS = list(range(0, 1200, 120))
DEFAULT_VARIANTS = ["V1_sim", "V1_sched", "V2_sched", "V2_obs", "V1_obs"]


def _switch_scales() -> dict[str, float]:
    """observed / predicted switching, from n8st.ledger.validate_flex (weekend N)."""
    p = PROCESSED_DIR / "flex_theta.json"
    if not p.exists():
        return {}
    cal = json.loads(p.read_text())
    return {"net_hours_flex_calibrated": cal.get("switch_scale_did"),
            "net_hours_flex_calibrated_raw": cal.get("switch_scale_raw")}


SCALES = {k: v for k, v in _switch_scales().items() if v}
FLEX_COLS = ["net_hours_flex_upper", "net_hours_flex_calibrated", "net_hours_flex_calibrated_raw"]


def run(od_path: Path, variants: list[str], offsets: list[int], step_s: int,
        hours: range, check: bool = False) -> dict:
    feed = gtfs.load(gtfs.GTFS_DIR / "subway_latest.zip")
    template = tt.segment_template(feed)
    cidx = engine.complex_index(network.from_feed(feed, "Weekday"), complexes_from_stations())
    area = flex.area_complexes(pl.read_parquet(STATIONS)).filter(
        pl.col("complex_id").is_in([int(c) for c in cidx.ids]))
    area_ids = area["complex_id"].to_list()
    od = load_od(od_path)
    weights = engine.GRID
    if check:
        scen_feeds = {f"pure_shift_{s}s": shift_route(feed, "N", s) for s in (60, 180)}
    else:
        scen_feeds = {v: tt.apply(feed, VARIANTS[v], template)[0] for v in variants}
    per_offset, by_hour, flows = [], [], []
    for d in offsets:
        t = time.monotonic()
        base = network.from_feed(shift_route(feed, "N", d), "Weekday")
        nets = {name: network.from_feed(shift_route(f, "N", d), "Weekday")
                for name, f in scen_feeds.items()}
        out = engine.run(base, nets, cidx, od, weights=weights, hours=hours, step_s=step_s,
                         progress=False, flex_destinations=None if check else area_ids,
                         flex_origins=None if check else area_ids)
        tot = out["totals"].with_columns(offset_s=pl.lit(d))
        if not check:
            labels = pl.DataFrame({"weight_index": list(range(len(weights))),
                                   "weights": [w.label for w in weights]})
            # deterministic choice = upper bound on switching; scaled by observed/predicted
            # switching (calibrated on the weekend N) = central estimate
            adj = flex.adjustments(od, out["flex"], out["flex_out"], area,
                                   [w.walk for w in weights], list(nets))
            adj = adj.join(labels, on="weight_index").select(
                "scenario", "weights", pl.col("adjustment_hours").alias("_adj"))
            tot = tot.join(adj, on=["scenario", "weights"], how="left").with_columns(
                net_hours_flex_upper=pl.col("net_hours") + pl.col("_adj"),
                **{col: pl.col("net_hours") + scale * pl.col("_adj")
                   for col, scale in SCALES.items()}).drop("_adj")
        per_offset.append(tot)
        try:  # extras (by hour, by flow) must never sink the main result
            by_hour.append(out["by_hour"].with_columns(offset_s=pl.lit(d)))
            if out["pairs"].height:
                flows.append(out["pairs"].group_by("scenario", "origin", "destination").agg(
                    riders=pl.col("riders").sum(),
                    hours=(pl.col("riders") * pl.col("d_cost_s")).sum() / 3600))
        except Exception as e:  # noqa: BLE001
            print(f"  extras failed at offset {d}: {e}", flush=True)
        print(f"  offset {d:>3} s done in {time.monotonic() - t:.0f} s", flush=True)
    extras = {}
    try:
        n = len(offsets)
        extras["by_hour"] = pl.concat(by_hour).group_by("scenario", "weights", "hour").agg(
            pl.col("net_hours").mean()).sort("scenario", "weights", "hour")
        if flows:
            # pairs only list (origin, destination, hour) cells that changed, so divide the
            # sum by the number of offsets rather than taking a mean
            extras["flows"] = pl.concat(flows).group_by("scenario", "origin", "destination").agg(
                riders=pl.col("riders").sum() / n, hours=pl.col("hours").sum() / n)
    except Exception as e:  # noqa: BLE001
        print(f"  extras aggregation failed: {e}", flush=True)
    allt = pl.concat(per_offset, how="diagonal_relaxed")
    value_cols = [c for c in ("net_hours", "hours_saved", "hours_lost", *FLEX_COLS,
                              "riders_affected") if c in allt.columns]
    avg = allt.group_by("scenario", "weights", "wait_w", "walk_w", "transfer_min").agg(
        *[pl.col(c).mean() for c in value_cols],
        *[pl.col(c).std().alias(f"{c}_sd_across_offsets") for c in value_cols[:1]],
    ).sort("scenario", "weights")
    return {"per_offset": allt, "average": avg, **extras}


def md(df: pl.DataFrame, digits: int = 0) -> str:
    df = df.with_columns(pl.col(pl.Float64).round(digits))
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(f"{v:,}" if isinstance(v, (int, float)) and not
                               isinstance(v, bool) else str(v) for v in r) + " |"
              for r in df.iter_rows()]
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--od", type=Path, default=Path(
        "data/raw/mta_data/bulk/od/od_weekday_2026_04.parquet"))
    p.add_argument("--variants", nargs="*", default=DEFAULT_VARIANTS)
    p.add_argument("--offsets", type=int, nargs="*", default=DEFAULT_OFFSETS)
    p.add_argument("--step", type=int, default=180)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    t0 = time.monotonic()
    res = run(args.od, args.variants, args.offsets, args.step, range(5, 24), args.check)
    avg = res["average"]
    tag = "check" if args.check else args.od.stem.replace("od_", "")
    folder = PROCESSED_DIR / f"ledger_phase_{tag}"
    folder.mkdir(parents=True, exist_ok=True)
    res["per_offset"].write_csv(folder / "per_offset.csv")
    avg.write_csv(folder / "totals.csv")
    try:
        if "by_hour" in res:
            res["by_hour"].write_csv(folder / "by_hour.csv")
        if "flows" in res:
            res["flows"].write_parquet(folder / "flows.parquet")
    except Exception as e:  # noqa: BLE001
        print(f"  writing extras failed: {e}", flush=True)
    (folder / "meta.json").write_text(json.dumps({
        "od": str(args.od), "offsets_s": args.offsets, "step_s": args.step,
        "variants": list(avg["scenario"].unique()), "runtime_s": round(time.monotonic() - t0)},
        indent=1))
    base = avg.filter(pl.col("weights") == engine.BASE.label).drop("weights")
    flex_present = [c for c in FLEX_COLS if c in avg.columns]
    cols = [c for c in ("scenario", "net_hours", "net_hours_sd_across_offsets", "hours_saved",
                        "hours_lost", *flex_present) if c in base.columns]
    n_off = len(args.offsets)
    base = base.with_columns(
        se=pl.col("net_hours_sd_across_offsets") / n_off ** 0.5)
    grid = avg.group_by("scenario").agg(
        cells=pl.len(), cells_saving=(pl.col("net_hours") < 0).sum(),
        **{f"cells_saving_{c.removeprefix('net_hours_')}": (pl.col(c) < 0).sum()
           for c in flex_present},
        best=pl.col("net_hours").min(), worst=pl.col("net_hours").max()).sort("scenario")
    text = "\n".join([
        "# Phase-averaged ledger" + (" (check: pure shifts)" if args.check else ""),
        "",
        f"OD `{args.od.name}`; N trips shifted by {args.offsets} s in both baseline and "
        f"scenario, results averaged; riders sampled every {args.step} s with jitter, "
        "5 am–midnight. `se` = standard error of the phase average.",
        "",
        "Columns: `net_hours` keeps today's stations; `flex_upper` lets every rider around "
        "campus take the cheapest station (upper bound on switching, which overpredicts the "
        "weekend switch about tenfold); `flex_calibrated` scales that switching benefit by "
        "observed ÷ predicted switching on weekends (difference-in-differences, central "
        "estimate); `flex_calibrated_raw` uses the raw weekend shift.",
        "",
        "## Base weights",
        "",
        md(base.select(*cols, "se")),
        "",
        "## Across the 13-cell weight grid",
        "",
        md(grid),
        "",
    ])
    out = FINDINGS_DIR / f"ledger_phase_{tag}.md"
    out.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
