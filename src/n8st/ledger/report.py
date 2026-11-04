"""Turn a ledger run into a findings page.

    python -m n8st.ledger.report data/processed/ledger_weekday_2026_09
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from n8st.config import FINDINGS_DIR
from n8st.ledger import engine
from n8st.ledger.run import STATIONS

HEADLINE = "V1_obs"
LABELS = {
    "V1_sched": "V1 N local 34 St–Canal, MTA weekend timing",
    "V1_obs": "V1 N local 34 St–Canal, observed weekday timing",
    "V1_wkend": "V1 N local 34 St–Canal, observed weekend timing",
    "V2_sched": "V2 N local 14 St–Canal only, schedule timing",
    "V2_obs": "V2 N local 14 St–Canal only, observed timing",
    "V4_obs": "V4 Q local instead of the N",
    "V5_obs": "V5 N local only 10–4 and 7–midnight",
}


def names() -> dict[int, str]:
    st = pl.read_parquet(STATIONS).select(
        pl.col("complex_id").cast(pl.Float64).cast(pl.Int64), "stop_name", "daytime_routes")
    agg = st.group_by("complex_id").agg(
        name=pl.col("stop_name").unique().sort().str.join(" / "),
        routes=pl.col("daytime_routes").str.join(" "))
    return {c: f"{n} ({' '.join(sorted(set(r.split())))})" for c, n, r in agg.iter_rows()}


def md(df: pl.DataFrame, digits: int = 0) -> str:
    df = df.with_columns(pl.col(pl.Float64, pl.Float32).round(digits))
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join("" if v is None else f"{v:,}" if isinstance(v, (int, float))
                               else str(v) for v in r) + " |" for r in df.iter_rows()]
    return "\n".join(lines)


def build(folder: Path) -> str:
    totals = pl.read_csv(folder / "totals.csv")
    by_hour = pl.read_csv(folder / "by_hour.csv")
    pairs = pl.read_parquet(folder / "pairs.parquet")
    meta = json.loads((folder / "meta.json").read_text())
    nm = names()
    base_label = engine.BASE.label

    head = (totals.filter(pl.col("weights") == base_label)
            .join(pl.DataFrame([{"scenario": k, "added_s_per_trip": v["median_added_s"],
                                 "trips_changed": v["trips"]}
                                for k, v in meta["variants"].items()]), on="scenario")
            .with_columns(pl.col("scenario").replace_strict(LABELS, default=pl.col("scenario"))
                          .alias("variant"))
            .select("variant", "trips_changed", "added_s_per_trip", "hours_saved",
                    "hours_lost", "net_hours")
            .sort("net_hours"))

    robust = (totals.group_by("scenario").agg(
        cells=pl.len(), cells_net_saving=(pl.col("net_hours") < 0).sum(),
        best_net=pl.col("net_hours").min(), worst_net=pl.col("net_hours").max())
        .with_columns(pl.col("scenario").replace_strict(LABELS, default=pl.col("scenario"))
                      .alias("variant"))
        .select("variant", "cells", "cells_net_saving", "best_net", "worst_net")
        .sort("best_net"))

    grid = (totals.filter(pl.col("scenario") == HEADLINE)
            .pivot(on="transfer_min", index="wait_w", values="net_hours").sort("wait_w")
            .with_columns(pl.col("wait_w").cast(pl.String)))
    grid.columns = ["wait & walk weight"] + [f"transfer {c} min" for c in grid.columns[1:]]

    p = pairs.filter(pl.col("scenario") == HEADLINE).with_columns(
        hours=pl.col("riders") * pl.col("d_cost_s") / 3600)
    gain_dest = (p.filter(pl.col("hours") < 0).group_by("destination")
                 .agg(riders=pl.col("riders").sum(), hours_saved=-pl.col("hours").sum(),
                      avg_min_saved=-(pl.col("d_cost_s") * pl.col("riders")).sum()
                      / pl.col("riders").sum() / 60)
                 .sort("hours_saved", descending=True).head(10)
                 .with_columns(pl.col("destination").replace_strict(nm, default="?")
                               .alias("destination")))
    gain_orig = (p.filter(pl.col("hours") < 0).group_by("origin")
                 .agg(riders=pl.col("riders").sum(), hours_saved=-pl.col("hours").sum())
                 .sort("hours_saved", descending=True).head(10)
                 .with_columns(pl.col("origin").replace_strict(nm, default="?").alias("origin")))
    lose_orig = (p.filter(pl.col("hours") > 0).group_by("origin")
                 .agg(riders=pl.col("riders").sum(), hours_lost=pl.col("hours").sum())
                 .sort("hours_lost", descending=True).head(10)
                 .with_columns(pl.col("origin").replace_strict(nm, default="?").alias("origin")))
    top_pairs = (p.group_by("origin", "destination")
                 .agg(riders=pl.col("riders").sum(), hours=pl.col("hours").sum(),
                      min_per_rider=(pl.col("d_cost_s") * pl.col("riders")).sum()
                      / pl.col("riders").sum() / 60))
    def named(df: pl.DataFrame) -> pl.DataFrame:
        return df.with_columns(pl.col("origin").replace_strict(nm, default="?"),
                               pl.col("destination").replace_strict(nm, default="?"))

    winners = named(top_pairs.sort("hours").head(12))
    losers = named(top_pairs.sort("hours", descending=True).head(12))

    hourly = (by_hour.filter(pl.col("weights") == base_label)
              .pivot(on="scenario", index="hour", values="net_hours").sort("hour"))

    out = [
        "# Scenario ledger: does an N stop at 8 St–NYU save riders time?",
        "",
        f"OD: `{Path(meta['od']).name}` ({meta['od_riders_per_day']:,.0f} weekday trips "
        f"between {meta['hours'][0]}:00 and {meta['hours'][-1] + 1}:00). Departures sampled "
        f"every {meta['step_s']} s; riders keep today's origin and destination stations "
        "(fixed OD), so benefits to riders who would *switch* to 8 St are not counted.",
        "",
        "Costs are generalized: in-train minutes + 2 × waiting + 2 × walking + 5 min per "
        "transfer (base weights). Negative net = riders save time overall.",
        "",
        "## Headline (base weights, passenger-hours per weekday)",
        "",
        md(head),
        "",
        "## Robustness across the 13-cell weight grid",
        "",
        "Wait/walk weight 1.5, 2, 2.5 × transfer penalty 0, 5, 10, 15 min, plus 2 × 30 min.",
        "",
        md(robust),
        "",
        f"## {LABELS[HEADLINE]}: net hours by weight",
        "",
        md(grid),
        "",
        f"## Who gains under {HEADLINE} (base weights)",
        "",
        "Destinations with the most hours saved:",
        "",
        md(gain_dest, 1),
        "",
        "Origins with the most hours saved:",
        "",
        md(gain_orig, 1),
        "",
        "Biggest winning flows (origin → destination):",
        "",
        md(winners.select("origin", "destination", "riders", "hours", "min_per_rider"), 1),
        "",
        f"## Who loses under {HEADLINE}",
        "",
        "Origins with the most hours lost:",
        "",
        md(lose_orig, 1),
        "",
        "Biggest losing flows:",
        "",
        md(losers.select("origin", "destination", "riders", "hours", "min_per_rider"), 1),
        "",
        "## Net hours by hour of the day (base weights)",
        "",
        md(hourly, 1),
        "",
    ]
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    text = build(args.folder)
    path = FINDINGS_DIR / f"{args.folder.name}.md"
    path.write_text(text)
    print(text)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
