"""Does the destination-flexibility model predict how riders actually switch stations?

The weekend N stops at 8 St-NYU, so weekends show what Sea Beach riders do when the
one-seat ride exists: their share choosing 8 St among campus-area stations rises from
2.9% (weekdays) to 7.0% (weekends), +2.5 points net of the West End comparison
(docs/findings/weekend_experiment.md).

Here the model predicts the same quantity: the share of Sea Beach riders bound for
campus-area stations whose best station is 8 St-NYU, today (weekday schedule) and under
V1 (the weekday N running local). If the predicted shift is close to the observed one,
the flexibility adjustment in the ledger is believable.

    python -m n8st.ledger.validate_flex --od data/raw/mta_data/bulk/od/od_weekday_2026_04.parquet
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from n8st.config import FINDINGS_DIR, PROCESSED_DIR, SEA_BEACH_STOPS
from n8st.data import gtfs
from n8st.ledger import engine, flex
from n8st.ledger.run import STATIONS, VARIANTS, complexes_from_stations, load_od
from n8st.routing import network
from n8st.scenarios import timetable as tt


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--od", type=Path, required=True)
    p.add_argument("--variant", default="V1_sim")
    args = p.parse_args()
    feed = gtfs.load(gtfs.GTFS_DIR / "subway_latest.zip")
    base = network.from_feed(feed, "Weekday")
    f2, _ = tt.apply(feed, VARIANTS[args.variant])
    scn = network.from_feed(f2, "Weekday")
    cidx = engine.complex_index(base, complexes_from_stations())
    stations = pl.read_parquet(STATIONS)
    area = flex.area_complexes(stations).filter(
        pl.col("complex_id").is_in([int(c) for c in cidx.ids]))
    sea = sorted(set(stations.filter(pl.col("gtfs_stop_id").is_in(SEA_BEACH_STOPS))[
        "complex_id"].cast(pl.Float64).cast(pl.Int64)))
    od = load_od(args.od).filter(pl.col("origin").is_in(sea))
    weights = engine.GRID
    out = engine.run(base, {args.variant: scn}, cidx, od, weights=weights,
                     hours=range(6, 22), flex_destinations=area["complex_id"].to_list(),
                     progress=False)
    rows = []
    for wi, w in enumerate(weights):
        b, s = flex.choice_shares(od, out["flex"], area, sea, args.variant, wi, w.walk, 16)
        rows.append({"weights": w.label, "today_pct": b, "with_V1_pct": s, "shift_pts": s - b})
    res = pl.DataFrame(rows)
    observed_raw, observed_did = 4.09, 2.54

    # Calibrate the logit scale theta (1/seconds) at base weights so the predicted shift
    # toward 8 St matches what riders do when the N actually stops there (weekends).
    bw = next(i for i, w in enumerate(weights) if w == engine.BASE)
    scan = []
    for theta in (1 / 60, 1 / 120, 1 / 180, 1 / 300, 1 / 450, 1 / 600, 1 / 900, 1 / 1200,
                  1 / 1800, 1 / 2700, 1 / 3600):
        shift = flex.logit_shift(od, out["flex"], area, sea, args.variant, bw,
                                 engine.BASE.walk, theta, 16)
        scan.append({"theta_per_s": theta, "one_over_theta_s": round(1 / theta),
                     "predicted_shift_pts": shift})
    scan_df = pl.DataFrame(scan)

    def pick(target):
        # interpolate one_over_theta where predicted shift crosses target (shift falls
        # as 1/theta grows, i.e. as choices get noisier)
        xs = scan_df["one_over_theta_s"].to_list()
        ys = scan_df["predicted_shift_pts"].to_list()
        for (x0, y0), (x1, y1) in zip(zip(xs, ys, strict=True), zip(xs[1:], ys[1:],
                                                                    strict=True), strict=False):
            if (y0 - target) * (y1 - target) <= 0 and y0 != y1:
                return x0 + (target - y0) * (x1 - x0) / (y1 - y0)
        return None

    det_shift = res.filter(pl.col("weights") == engine.BASE.label)["shift_pts"].item()
    cal = {"did_target_pts": observed_did, "raw_target_pts": observed_raw,
           "deterministic_predicted_shift_pts": det_shift,
           # Scale factors for the deterministic switching benefit: observed / predicted.
           "switch_scale_did": observed_did / det_shift,
           "switch_scale_raw": observed_raw / det_shift,
           "one_over_theta_did_s": pick(observed_did), "one_over_theta_raw_s": pick(observed_raw)}
    (PROCESSED_DIR / "flex_theta.json").write_text(json.dumps(cal, indent=1))

    def md(df):
        lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
        lines += ["| " + " | ".join(f"{v:.4g}" if isinstance(v, float) else str(v) for v in r)
                  + " |" for r in df.iter_rows()]
        return "\n".join(lines)

    text = "\n".join([
        "# Validating destination flexibility against the weekend N",
        "",
        "Predicted share of Sea Beach (N) riders bound for campus-area stations who use "
        "8 St–NYU, weekday OD, 6 am–10 pm, today and with the weekday N running local.",
        "",
        "## Deterministic choice (everyone takes the cheapest station)",
        "",
        md(res),
        "",
        f"Observed (weekends, when the N runs local): **+{observed_raw:.2f} points** raw, "
        f"**+{observed_did:.2f}** net of the West End comparison. Deterministic choice "
        "overpredicts switching roughly tenfold, so it is only an upper bound.",
        "",
        "## Logit choice, calibrated",
        "",
        "P(station) ∝ exp(−θ × cost). Smaller θ (larger 1/θ) = noisier, stickier choices. "
        "Predicted shift at base weights:",
        "",
        md(scan_df),
        "",
        f"Calibrated 1/θ: **{cal['one_over_theta_did_s'] or float('nan'):.0f} s** to match "
        f"the difference-in-differences (+{observed_did}), "
        f"**{cal['one_over_theta_raw_s'] or float('nan'):.0f} s** to match the raw weekend "
        f"shift (+{observed_raw}).",
        "",
        "A logit this noisy gives every rider a few percent chance of every station near "
        "campus, so its logsum benefit credits the 8 St improvement to almost everyone "
        "(in tests it exceeded even the deterministic upper bound). The ledger therefore "
        "uses a simpler, transparent calibration: the deterministic switching benefit "
        "scaled by observed ÷ predicted switching, "
        f"**{cal['switch_scale_did']:.3f}** (difference-in-differences) to "
        f"**{cal['switch_scale_raw']:.3f}** (raw).",
        "",
    ])
    (FINDINGS_DIR / "flex_validation.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
