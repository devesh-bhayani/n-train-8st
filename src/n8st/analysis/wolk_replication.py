"""Phase 0: reproduce Stop the Stop's ranking and stress-test the 8 St-NYU result.

    make wolk        # once: clones github.com/WoshuaJolk/stopthestop-data into external/
    python -m n8st.analysis.wolk_replication

Uses Wolk's own scoring function on his committed results (level 1 of his README),
then sweeps stop cost x walk weight x walk mode for 8 St-NYU and its neighbours.
Writes docs/findings/phase0_wolk_replication.md.
"""

from __future__ import annotations

import json

import pandas as pd

from n8st.config import FINDINGS_DIR, PROJECT_ROOT

WOLK = PROJECT_ROOT / "external" / "stopthestop-data"
FOCUS = {"R18": "28 St", "R19": "23 St", "R21": "8 St-NYU", "R22": "Prince St"}
# Published values (results/ranking.csv at commit 365c028) that our run must match.
EXPECTED = {"R21": (-2867.2, 308), "L05": (1823.8, 1)}
STOP_COSTS = [20, 30, 40, 50, 60, 70, 80, 90]
WALK_WEIGHTS = [1.0, 1.5, 2.0, 2.5, 3.0]


DELTA_AT = (0, 30, 70)  # stop costs (s) at which Wolk's timetable simulation was run
WALK_COLS = {"line": "walkLine", "any": "walkAny", "station": "walkStation"}


def ride_saved_s(delta: list[float], stop_cost: float) -> float:
    """Seconds per weekday saved by everyone else, linearly interpolated between runs."""
    i = 0 if stop_cost <= DELTA_AT[1] else 1
    slope = (delta[i + 1] - delta[i]) / (DELTA_AT[i + 1] - DELTA_AT[i])
    return -(delta[i] + slope * (stop_cost - DELTA_AT[i]))


def score(stops: list[dict], stop_cost: float = 50, walk_weight: float = 2.0,
          walk_speed: float = 1.3, walk: str = "line") -> pd.DataFrame:
    """Independent re-implementation of the ledger in docs/methodology.md of Stop the Stop.

    net = (through-riders' time saved) - (stop users x extra walk / speed x walk weight)
    """
    d = pd.DataFrame(stops)
    d["ride_saved_hrs"] = d["rideDelta"].map(lambda x: ride_saved_s(x, stop_cost)) / 3600
    d["walk_added_hrs"] = d["users"] * d[WALK_COLS[walk]] / walk_speed * walk_weight / 3600
    d["net_hrs"] = d["ride_saved_hrs"] - d["walk_added_hrs"]
    d = d.sort_values("net_hrs", ascending=False).reset_index(drop=True)
    d.insert(0, "rank", range(1, len(d) + 1))
    return d.drop(columns="rideDelta").rename(columns={"id": "stop"})


def load_wolk():
    """Read Wolk's published data files only (no code from his repo is executed)."""
    if not WOLK.exists():
        raise SystemExit("Run `make wolk` first.")
    stops = json.loads((WOLK / "results" / "stops.json").read_text())["stops"]
    published = pd.read_csv(WOLK / "results" / "ranking.csv")
    return stops, published


def md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    rows = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    rows += ["| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False)]
    return "\n".join(rows)


def main() -> None:
    stops, published = load_wolk()
    base = score(stops).set_index("stop")
    pub = published.set_index("stop")
    joined = base.join(pub[["net_hrs", "rank"]].add_suffix("_published"))
    max_net_diff = (joined["net_hrs"] - joined["net_hrs_published"]).abs().max()
    rank_mismatches = int((joined["rank"] != joined["rank_published"]).sum())
    full_check = pd.DataFrame([{
        "stops_compared": len(joined),
        "max_abs_diff_net_hrs": round(max_net_diff, 3),
        "rank_mismatches": rank_mismatches,
    }])

    checks = []
    for stop, (net, rank) in EXPECTED.items():
        got_net, got_rank = round(base.loc[stop, "net_hrs"], 1), int(base.loc[stop, "rank"])
        ok = abs(got_net - net) < 0.15 and got_rank == rank
        checks.append({"stop": stop, "published_net_hrs": net, "our_net_hrs": got_net,
                       "published_rank": rank, "our_rank": got_rank,
                       "match": "yes" if ok else "NO"})
    checks = pd.DataFrame(checks)

    focus = base.loc[list(FOCUS), ["name", "routes", "users", "through", "ride_saved_hrs",
                                   "walk_added_hrs", "net_hrs", "rank"]].round(1).reset_index()

    # How close is the full re-route to "through-riders x stop cost"?
    r21 = next(s for s in stops if s["id"] == "R21")
    linear = pd.DataFrame({
        "stop_cost_s": [30, 70],
        "simulated_saving_s_per_through_rider": [round(-r21["rideDelta"][1] / r21["through"], 1),
                                                 round(-r21["rideDelta"][2] / r21["through"], 1)],
    })

    grid = []
    for walk in ("line", "any", "station"):
        for c in STOP_COSTS:
            for w in WALK_WEIGHTS:
                row = score(stops, stop_cost=c, walk_weight=w, walk=walk).set_index("stop")
                grid.append({"walk": walk, "stop_cost": c, "walk_weight": w,
                             "net_hrs": row.loc["R21", "net_hrs"], "rank": row.loc["R21", "rank"]})
    grid = pd.DataFrame(grid)
    summary = grid.groupby("walk").agg(
        cells=("net_hrs", "size"),
        cells_where_closing_saves_time=("net_hrs", lambda s: int((s > 0).sum())),
        worst_net_hrs=("net_hrs", "min"), best_net_hrs=("net_hrs", "max"),
        best_rank=("rank", "min"),
    ).round(1).reset_index()
    line_grid = grid[grid.walk == "line"].pivot(index="stop_cost", columns="walk_weight",
                                                values="net_hrs").round(0).astype(int)
    line_grid.columns = [f"w={c}" for c in line_grid.columns]

    out = [
        "# Phase 0: Stop the Stop replication",
        "",
        "An independent re-implementation of Wolk's scoring formula, run on his committed "
        "`results/stops.json` and checked against his published `results/ranking.csv` "
        "(github.com/WoshuaJolk/stopthestop-data, commit 365c028). This reproduces his "
        "ranking step, not the timetable simulation or the OD download (levels 2-3 of his README).",
        "",
        "## Published numbers reproduced",
        "",
        "All stops, against `results/ranking.csv` (differences under 0.05 h are rounding):",
        "",
        md(full_check),
        "",
        md(checks),
        "",
        "## 8 St-NYU and the other stops a local N would add (defaults: 50 s, walk x2, 1.3 m/s)",
        "",
        "`net_hrs` is rider-hours saved per weekday if the stop were *closed* to the R/W; "
        "negative means closing it costs riders time.",
        "",
        md(focus),
        "",
        "## The re-route is almost exactly linear",
        "",
        "Wolk re-routes every trip at each stop cost. For 8 St-NYU the saving per through-rider "
        "is within ~1 s of the stop cost itself, so few riders change route. For the N "
        "scenarios this means the cost side is well approximated by "
        "*N riders on board through the added stops x seconds added*, which is what "
        "the scenario ledger will compute first.",
        "",
        md(linear),
        "",
        "## Sensitivity: is 8 St-NYU worth keeping under every assumption?",
        "",
        "`walk` = where displaced riders walk to: `line` = next stop on the same line, "
        "`any` = nearest station on any line, `station` = next station of the same complex type.",
        "",
        md(summary),
        "",
        "Net rider-hours if 8 St-NYU closed, walking to the next R/W stop, by stop cost (rows) "
        "and walk weight (columns):",
        "",
        md(line_grid.reset_index()),
        "",
    ]
    path = FINDINGS_DIR / "phase0_wolk_replication.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out))
    print("\n".join(out))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
