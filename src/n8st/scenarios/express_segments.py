"""Find every express run in the network: stretches where a route skips stations that a
local route on the same line serves. Each becomes a candidate "run it local" scenario.

    python -m n8st.scenarios.express_segments

Detection, per route and direction (weekday, most common stop pattern):
  - take consecutive stops (a, b) of the express route E
  - find a local route L whose own pattern contains a ... b with at least one station in
    between (by station complex, so platform differences at a junction don't matter)
  - merge consecutive skipped stretches into one maximal express run
The candidate scenario inserts the skipped stations into every weekday trip of E,
timed with L's own scheduled segment times (the local's timing, as V1 does with the
weekend N). Physical feasibility (crossovers at both ends) is NOT checked here: every
row of the screen needs a track-map check before it means anything.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import polars as pl


@dataclass(frozen=True)
class ExpressRun:
    route: str
    direction: str
    stops: tuple[str, ...]  # the express route's parent stops, first..last of the run
    inserted: tuple[str, ...]  # local stations skipped in between, in order
    local_route: str

    @property
    def name(self) -> str:
        return f"{self.route}_{self.direction}_{self.stops[0]}-{self.stops[-1]}"


def typical_patterns(feed: dict[str, pl.DataFrame], service_id: str = "Weekday"
                     ) -> dict[tuple[str, str], list[str]]:
    trips = feed["trips"].filter(pl.col("service_id") == service_id).select("trip_id",
                                                                            "route_id")
    st = feed["stop_times"].join(trips, on="trip_id").sort("trip_id", "stop_sequence")
    seqs = st.group_by("trip_id", maintain_order=True).agg(
        pl.col("route_id").first(), pl.col("direction").first(), pl.col("parent_stop"),
        dep=pl.col("dep_s").first())
    # daytime trips only, so late-night local patterns don't count as "typical"
    seqs = seqs.filter(pl.col("dep").is_between(6 * 3600, 21 * 3600))
    out: dict[tuple[str, str], list[str]] = {}
    for (route, direction), grp in seqs.group_by("route_id", "direction"):
        counts = Counter(tuple(p) for p in grp["parent_stop"].to_list())
        # ties broken by the pattern itself, so the result never depends on row order
        common = max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0]
        out[(route, direction)] = list(common)
    return dict(sorted(out.items()))


MAX_DETOUR = 1.25  # the local's path may be at most 25% longer than the express hop


def _km(a, b) -> float:
    import math

    (la1, lo1), (la2, lo2) = a, b
    x = math.radians(lo2 - lo1) * math.cos(math.radians((la1 + la2) / 2))
    y = math.radians(la2 - la1)
    return 6371 * math.hypot(x, y)


def find_runs(patterns: dict[tuple[str, str], list[str]], complex_of: dict[str, int],
              coords: dict[str, tuple[float, float]] | None = None) -> list[ExpressRun]:
    """coords: parent stop -> (lat, lon). When given, a local path between a and b only
    counts if it is at most MAX_DETOUR times the straight a-b distance (so a route over
    the Manhattan Bridge doesn't "skip" stations on the Montague tunnel route)."""
    def cx(s):
        return complex_of.get(s, s)

    def same_corridor(express_a, express_b, local_path) -> bool:
        # Same physical line: at least one end must be the very same station, not just the
        # same complex (the 6 at Canal/Union Sq shares complexes with the Broadway line).
        if express_a != local_path[0] and express_b != local_path[-1]:
            return False
        if not coords or any(s not in coords for s in (express_a, express_b, *local_path)):
            return True
        direct = _km(coords[express_a], coords[express_b])
        along = sum(_km(coords[p], coords[q]) for p, q in zip(local_path[:-1], local_path[1:],
                                                                strict=True))
        return direct > 0 and along <= MAX_DETOUR * direct + 0.3

    # Sorted iteration: with dict order, ties between equally long locals (the R and the W
    # under the N) went to whichever polars grouped first, and the screen changed between
    # runs (74-78 stretches). Now the longest local wins, ties to the first route name.
    runs: list[ExpressRun] = []
    for (route, direction), stops in sorted(patterns.items()):
        i = 0
        while i < len(stops) - 1:
            best = None
            for (lroute, ldir), lstops in sorted(patterns.items()):
                if ldir != direction or lroute == route:
                    continue
                lcx = [cx(s) for s in lstops]
                a, b = cx(stops[i]), cx(stops[i + 1])
                if a in lcx and b in lcx:
                    ia, ib = lcx.index(a), lcx.index(b)
                    if ib - ia >= 2 and same_corridor(stops[i], stops[i + 1],
                                                      lstops[ia:ib + 1]):
                        cand = (lroute, lstops[ia:ib + 1])
                        if best is None or len(cand[1]) > len(best[1]):
                            best = cand
            if best is None:
                i += 1
                continue
            # extend the run while the next express hop is also skipped by the same local
            lroute, lseg = best
            run_stops = [stops[i], stops[i + 1]]
            inserted = list(lseg[1:-1])
            lstops = patterns[(lroute, direction)]
            lcx = [cx(s) for s in lstops]
            j = i + 1
            while j < len(stops) - 1:
                a, b = cx(stops[j]), cx(stops[j + 1])
                if (a in lcx and b in lcx and lcx.index(b) - lcx.index(a) >= 2
                        and same_corridor(stops[j], stops[j + 1],
                                          lstops[lcx.index(a):lcx.index(b) + 1])):
                    run_stops.append(stops[j + 1])
                    inserted += lstops[lcx.index(a) + 1:lcx.index(b)]
                    j += 1
                else:
                    break  # the run ends where express and local stop together again
            runs.append(ExpressRun(route, direction, tuple(run_stops), tuple(inserted),
                                   lroute))
            i = j
    return runs


def main() -> None:
    from n8st.data import gtfs
    from n8st.ledger.run import STATIONS

    feed = gtfs.load(gtfs.GTFS_DIR / "subway_latest.zip")
    raw = pl.read_parquet(STATIONS)
    st = raw.select("gtfs_stop_id", pl.col("complex_id").cast(pl.Float64).cast(pl.Int64))
    complex_of = dict(st.iter_rows())
    coords = {g: (float(a), float(b)) for g, a, b in raw.select(
        "gtfs_stop_id", "gtfs_latitude", "gtfs_longitude").iter_rows()}
    runs = find_runs(typical_patterns(feed), complex_of, coords)
    df = pl.DataFrame([{"name": r.name, "route": r.route, "direction": r.direction,
                        "from": r.stops[0], "to": r.stops[-1], "skipped": len(r.inserted),
                        "local": r.local_route, "inserted": " ".join(r.inserted)}
                       for r in runs]).sort("route", "direction", "from")
    with pl.Config(tbl_rows=100, fmt_str_lengths=60):
        print(df)


if __name__ == "__main__":
    main()
