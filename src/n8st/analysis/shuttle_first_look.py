"""What the NYU shuttle network looks like from Union Square, from the logged Passio metadata.

    make shuttle-pull
    python -m n8st.analysis.shuttle_first_look [--dir data/raw/shuttle_remote]

Writes docs/findings/shuttle_first_look.md. Re-run as data accumulates; the headway
section fills in once there are a few days of positions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from n8st.config import FINDINGS_DIR, RAW_DIR
from n8st.shuttle import headways as hw
from n8st.shuttle.passio import parse_stops

CAMPUS_STOP_NAME = "715 Broadway"  # NYU building at Broadway & Washington Pl, by 8 St-NYU


def latest(meta_dir: Path, kind: str) -> dict:
    files = sorted(meta_dir.glob(f"date=*/{kind}-*.json"))
    if not files:
        raise FileNotFoundError(f"no {kind} snapshots in {meta_dir}")
    return json.loads(files[-1].read_text())


def route_names(routes_raw: dict | list) -> dict[str, str]:
    rows = routes_raw.get("all", routes_raw) if isinstance(routes_raw, dict) else routes_raw
    names = {}
    for r in rows if isinstance(rows, list) else []:
        for key in ("myid", "id"):
            if r.get(key) is not None:
                names[str(r[key])] = r.get("name")
    return names


def md(df: pl.DataFrame) -> str:
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |"
              for r in df.iter_rows()]
    return "\n".join(lines)


def build(shuttle_dir: Path) -> str:
    stops_list, route_stops_list = parse_stops(latest(shuttle_dir / "meta", "stops"))
    names = route_names(latest(shuttle_dir / "meta", "routes"))
    stops = pl.DataFrame(stops_list)
    route_stops = pl.DataFrame(route_stops_list).with_columns(
        route=pl.col("route_id").replace_strict(names, default=pl.col("route_id"))
    )
    stop_name = dict(zip(stops["stop_id"], stops["name"], strict=True))

    near = hw.stops_near(stops, within_m=600).with_columns(pl.col("dist_m").round(0).cast(int))
    served = (
        route_stops.filter(pl.col("stop_id").is_in(near["stop_id"].implode()))
        .group_by("stop_id").agg(routes=pl.col("route").unique().sort().str.join(", "))
    )
    near = near.join(served, on="stop_id", how="left").select(
        "stop_id", "name", "dist_m", "routes").sort("dist_m")

    # Which routes run from a Union Square-area stop to the campus stop, and how many stops?
    campus_ids = stops.filter(pl.col("name") == CAMPUS_STOP_NAME)["stop_id"].to_list()
    legs = []
    for route_id, grp in route_stops.group_by("route_id"):
        order = grp.sort("position")["stop_id"].to_list()
        for i, sid in enumerate(order):
            if sid not in set(near["stop_id"]):
                continue
            for j in range(i + 1, len(order)):
                if order[j] in campus_ids:
                    legs.append({"route": names.get(str(route_id[0]), route_id[0]),
                                 "board_at": stop_name.get(sid), "alight_at": CAMPUS_STOP_NAME,
                                 "stops_in_between": j - i - 1})
                    break
    legs_df = (pl.DataFrame(legs).sort("stops_in_between") if legs
               else pl.DataFrame({"note": ["no route found"]}))

    out = [
        "# NYU shuttle: first look from Union Square",
        "",
        f"From the latest Passio GO metadata snapshot in `{shuttle_dir}`.",
        "",
        "## Shuttle stops within 600 m of the 14 St-Union Sq subway (Broadway line)",
        "",
        md(near),
        "",
        f"## Routes from those stops to {CAMPUS_STOP_NAME} (next to 8 St-NYU)",
        "",
        md(legs_df),
        "",
        "## Stop order on each campus route",
        "",
    ]
    for route_id, grp in sorted(route_stops.group_by("route_id"), key=lambda g: str(g[0][0])):
        name = names.get(str(route_id[0]), route_id[0])
        seq = [stop_name.get(s, s) for s in grp.sort("position")["stop_id"]]
        out.append(f"- **{name}**: " + " → ".join(seq))
    out.append("")

    try:
        v = hw.load_vehicles(shuttle_dir)
        fleet = (
            v.group_by("route_name").agg(
                buses_seen=pl.col("vehicle_key").n_unique(),
                capacity=pl.col("capacity").max() if "capacity" in v.columns else pl.lit(None),
                position_rows=pl.len(),
            ).sort("route_name")
        )
        out += ["## Buses seen so far", "", md(fleet), ""]
        visits = hw.stop_visits(v, hw.stops_near(stops, within_m=600))
        summary = hw.headway_summary(hw.headways(visits))
        out += ["## Headways at Union Square-area stops (needs a few days of data)", ""]
        out.append(md(summary) if summary.height else "Not enough visits yet.")
        out.append("")
    except Exception as e:  # no vehicle data yet
        out += [f"_No vehicle data yet: {e}_", ""]
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", type=Path, default=RAW_DIR / "shuttle_remote")
    args = parser.parse_args()
    report = build(args.dir)
    path = FINDINGS_DIR / "shuttle_first_look.md"
    path.write_text(report)
    print(report)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
