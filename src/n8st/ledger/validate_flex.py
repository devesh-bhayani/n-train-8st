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
from pathlib import Path

import polars as pl

from n8st.config import FINDINGS_DIR, SEA_BEACH_STOPS
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
    lines = ["| " + " | ".join(res.columns) + " |", "|" + "---|" * len(res.columns)]
    lines += ["| " + " | ".join(f"{v:.2f}" if isinstance(v, float) else str(v) for v in r)
              + " |" for r in res.iter_rows()]
    text = "\n".join([
        "# Validating destination flexibility against the weekend N",
        "",
        "Predicted share of Sea Beach (N) riders bound for campus-area stations who use "
        "8 St–NYU, weekday OD, 6 am–10 pm, today and with the weekday N running local.",
        "",
        *lines,
        "",
        f"Observed (weekends, when the N runs local): **+{observed_raw:.2f} points** raw, "
        f"**+{observed_did:.2f}** net of the West End comparison. Today's weekday share "
        "observed: 2.91%.",
        "",
    ])
    (FINDINGS_DIR / "flex_validation.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
