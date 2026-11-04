"""Run the scenario ledger on real MTA data.

    make mta-pull                       # OD matrices + stations from the mta-data branch
    python -m n8st.ledger.run --od data/raw/mta_data/bulk/od/od_weekday_2026_09.parquet

Scenario variants (timing of the inserted local stops, per through-rider):
    V1_sim     calibrated simulation: 185 s downtown, 110 s uptown, R/W/Q knock-on  <- headline
    V1_sched   MTA's own weekend local schedule (~150 s)
    V1_obs     observed weekday local-track running + crossover (~210 s)
    V1_wkend   observed weekend local N (~260 s)
    V2_sched / V2_obs   express to 14 St, then local 8 St + Prince (~90 s / ~110 s)
    V4_obs     the Q runs local instead of the N
    V5_obs     V1_obs only 10 am-4 pm and 7 pm-midnight
    V6_W       no pattern change: 8 more Sea Beach W trips (n8st.scenarios.extra_trips)

Observed values come from docs/findings/observed_service.md (subwaydata.nyc, Sep-Oct 2026).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import duckdb
import polars as pl

from n8st.config import PROCESSED_DIR, RAW_DIR
from n8st.data import gtfs
from n8st.ledger import engine, flex
from n8st.routing import network
from n8st.scenarios import extra_trips
from n8st.scenarios import timetable as tt

STATIONS = RAW_DIR / "mta_data" / "bulk" / "stations" / "stations.parquet"

# Per-inserted-stop penalties that reproduce the observed segment differences.
OBS_V1_PER_STOP = 210 / 4
WKEND_V1_PER_STOP = 262 / 4
OBS_V2_PER_STOP = 110 / 2

VARIANTS: dict[str, tt.Scenario] = {
    "V1_sched": tt.Scenario("V1_sched"),
    "V1_obs": tt.Scenario("V1_obs", timing="penalty", penalty_s=OBS_V1_PER_STOP),
    "V1_wkend": tt.Scenario("V1_wkend", timing="penalty", penalty_s=WKEND_V1_PER_STOP),
    "V2_sched": tt.Scenario("V2_sched", insert=("R21", "R22")),
    "V2_obs": tt.Scenario("V2_obs", insert=("R21", "R22"), timing="penalty",
                          penalty_s=OBS_V2_PER_STOP),
    "V4_obs": tt.Scenario("V4_obs", route="Q", timing="penalty", penalty_s=OBS_V1_PER_STOP),
    "V5_obs": tt.Scenario("V5_obs", timing="penalty", penalty_s=OBS_V1_PER_STOP,
                          hours=tuple(range(10, 16)) + tuple(range(19, 24))),
    # From the calibrated SimPy simulation (docs/findings/simulation.md): extra time for
    # the N by direction, plus knock-on delay to the R/W and relief for the Q.
    "V1_sim": tt.Scenario(
        "V1_sim", timing="penalty", added_by_direction={"S": 185, "N": 110},
        knock_on=(("R", "S", 9), ("W", "S", 7), ("Q", "S", -26),
                  ("R", "N", 10), ("W", "N", 9), ("Q", "N", -38))),
}


# Variants that add trips instead of stops.
EXTRA_TRIP_VARIANTS = {"V6_W": extra_trips.apply_v6}


def variant_feed(feed: dict[str, pl.DataFrame], name: str,
                 template: dict | None = None) -> dict[str, pl.DataFrame]:
    """The scenario timetable for any named variant."""
    if name in EXTRA_TRIP_VARIANTS:
        return EXTRA_TRIP_VARIANTS[name](feed)[0]
    return tt.apply(feed, VARIANTS[name], template)[0]


def complexes_from_stations(path: Path = STATIONS) -> pl.DataFrame:
    st = pl.read_parquet(path).select(
        pl.col("complex_id").cast(pl.Float64).cast(pl.Int64),
        pl.col("gtfs_stop_id").cast(pl.String),
    )
    return st.group_by("complex_id").agg(gtfs_stop_ids=pl.col("gtfs_stop_id").str.join(" "))


def load_od(path: Path) -> pl.DataFrame:
    return pl.from_arrow(duckdb.sql(
        f"SELECT CAST(origin AS INT) AS origin, CAST(destination AS INT) AS destination, "
        f"CAST(hour AS INT) AS hour, CAST(riders AS DOUBLE) AS riders FROM '{path}' "
        f"WHERE origin <> destination"
    ).arrow())


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--od", type=Path, required=True)
    p.add_argument("--gtfs", type=Path, default=gtfs.GTFS_DIR / "subway_latest.zip")
    p.add_argument("--variants", nargs="*", default=list(VARIANTS))
    p.add_argument("--step", type=int, default=120, help="seconds between sampled departures")
    p.add_argument("--hours", type=int, nargs=2, default=(5, 24))
    p.add_argument("--limit-origins", type=int, default=0, help="for quick tests")
    args = p.parse_args(argv)

    t_start = time.monotonic()
    feed = gtfs.load(args.gtfs)
    template = tt.segment_template(feed)
    base = network.from_feed(feed, "Weekday")
    nets, trip_changes = {}, {}
    for name in args.variants:
        f2, summary = tt.apply(feed, VARIANTS[name], template)
        nets[name] = network.from_feed(f2, "Weekday")
        trip_changes[name] = {"trips": summary.height,
                              "median_added_s": summary["added_s"].median(),
                              "mean_added_s": summary["added_s"].mean()}
    cidx = engine.complex_index(base, complexes_from_stations())
    od = load_od(args.od)
    if args.limit_origins:
        keep = od["origin"].unique().sort().head(args.limit_origins).to_list()
        od = od.filter(pl.col("origin").is_in(keep))
    hours = range(args.hours[0], args.hours[1])
    print(f"OD rows {od.height:,}, riders/day {od['riders'].sum():,.0f}; "
          f"{len(cidx.ids)} complexes; variants {list(nets)}", flush=True)

    area = flex.area_complexes(pl.read_parquet(STATIONS))
    area = area.filter(pl.col("complex_id").is_in([int(c) for c in cidx.ids]))
    area_ids = area["complex_id"].to_list()
    out = engine.run(base, nets, cidx, od, hours=hours, step_s=args.step,
                     flex_destinations=area_ids, flex_origins=area_ids)

    # Destination flexibility around campus (n8st.ledger.flex).
    adj = flex.adjustments(od, out["flex"], out["flex_out"], area,
                           [w.walk for w in engine.GRID], list(nets))
    labels = pl.DataFrame({"weight_index": list(range(len(engine.GRID))),
                           "weights": [w.label for w in engine.GRID]})
    adj = adj.join(labels, on="weight_index").drop("weight_index")
    totals = out["totals"].join(adj.select("scenario", "weights", "adjustment_hours"),
                                on=["scenario", "weights"], how="left").with_columns(
        net_hours_flexible=pl.col("net_hours") + pl.col("adjustment_hours").fill_null(0))

    tag = args.od.stem.replace("od_", "")
    folder = PROCESSED_DIR / f"ledger_{tag}"
    folder.mkdir(parents=True, exist_ok=True)
    out["pairs"].write_parquet(folder / "pairs.parquet")
    totals.write_csv(folder / "totals.csv")
    adj.write_csv(folder / "flex_adjustments.csv")
    out["by_hour"].write_csv(folder / "by_hour.csv")
    out["totals"] = totals
    meta = {"od": str(args.od), "od_riders_per_day": od["riders"].sum(), "hours": list(hours),
            "step_s": args.step, "variants": trip_changes,
            "runtime_s": round(time.monotonic() - t_start)}
    (folder / "meta.json").write_text(json.dumps(meta, indent=1, default=str))
    print(json.dumps(meta, indent=1, default=str))
    print(out["totals"].filter(pl.col("weights") == engine.BASE.label))
    print(f"wrote {folder}; findings: python -m n8st.ledger.report {folder}")


if __name__ == "__main__":
    main()
