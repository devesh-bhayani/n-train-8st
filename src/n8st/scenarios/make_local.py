"""Generic "run this express stretch local" timetable edit, for the system-wide screen.

For an ExpressRun (see express_segments), every weekday trip of the express route that
runs the stretch gets the local route's stations inserted, timed with the local route's
own median scheduled segment times (daytime), and everything after the stretch shifted
by the extra time. This is the same idea as V1's template timing, generalized.
"""

from __future__ import annotations

import polars as pl

from n8st.scenarios.express_segments import ExpressRun

# Floor on the time an added stop costs: the pre-registered base stop penalty
# (docs/preregistration.md). Without it, a local whose schedule has less padding than the
# express made some stretches *faster* with more stops (e.g. the N at DeKalb Av, -30 s).
MIN_STOP_PENALTY_S = 45.0


def segment_medians(feed: dict[str, pl.DataFrame], service_id: str = "Weekday"
                    ) -> dict[tuple[str, str, str, str], float]:
    """{(route, direction, from_parent, to_parent): median scheduled seconds}, daytime."""
    trips = feed["trips"].filter(pl.col("service_id") == service_id).select("trip_id",
                                                                            "route_id")
    st = (feed["stop_times"].join(trips, on="trip_id").sort("trip_id", "stop_sequence")
          .with_columns(nxt=pl.col("parent_stop").shift(-1).over("trip_id"),
                        dt=pl.col("arr_s").shift(-1).over("trip_id") - pl.col("dep_s"))
          .drop_nulls("nxt").filter(pl.col("dep_s").is_between(6 * 3600, 21 * 3600)))
    med = st.group_by("route_id", "direction", "parent_stop", "nxt").agg(pl.col("dt").median())
    return {(r, d, a, b): float(t) for r, d, a, b, t in med.iter_rows()}


def local_path(run: ExpressRun, patterns: dict, complex_of: dict) -> list[str] | None:
    lp = patterns.get((run.local_route, run.direction))
    if not lp:
        return None

    def cx(s):
        return complex_of.get(s, s)

    lcx = [cx(s) for s in lp]
    a, b = cx(run.stops[0]), cx(run.stops[-1])
    if a not in lcx or b not in lcx:
        return None
    ia, ib = lcx.index(a), lcx.index(b)
    return lp[ia:ib + 1] if ib > ia else None


def apply_run(feed: dict[str, pl.DataFrame], run: ExpressRun, patterns: dict,
              complex_of: dict, medians: dict, service_id: str = "Weekday"
              ) -> tuple[dict[str, pl.DataFrame], pl.DataFrame]:
    path = local_path(run, patterns, complex_of)
    if path is None:
        return feed, pl.DataFrame()
    interior = path[1:-1]
    hops = list(zip([run.stops[0], *interior], [*interior, run.stops[-1]], strict=True))

    def hop_time(a, b):
        key = (run.local_route, run.direction, a, b)
        if key in medians:
            return medians[key]
        # endpoints on a different level of the same complex (e.g. Canal bridge vs local):
        # use the local's hop to its own end station
        if b == run.stops[-1]:
            return medians.get((run.local_route, run.direction, a, path[-1]))
        if a == run.stops[0]:
            return medians.get((run.local_route, run.direction, path[0], b))
        return None

    times_rel = []
    acc = 0.0
    for a, b in hops:
        t = hop_time(a, b)
        if t is None:
            return feed, pl.DataFrame()
        acc += t
        times_rel.append(acc)

    trips = feed["trips"].filter((pl.col("route_id") == run.route)
                                 & (pl.col("service_id") == service_id))["trip_id"].to_list()
    st = feed["stop_times"]
    affected = st.filter(pl.col("trip_id").is_in(trips) & (pl.col("direction") == run.direction))
    keep = st.join(affected.select("trip_id").unique(), on="trip_id", how="anti")
    new_parts, summary = [], []
    for (trip_id,), rows in affected.group_by("trip_id"):
        rows = rows.sort("stop_sequence")
        parents = rows["parent_stop"].to_list()
        try:
            i0 = parents.index(run.stops[0])
        except ValueError:
            new_parts.append(rows)
            continue
        if parents[i0:i0 + len(run.stops)] != list(run.stops):
            new_parts.append(rows)
            continue
        i1 = i0 + len(run.stops) - 1
        t0 = float(rows["dep_s"][i0])
        express_s = float(rows["arr_s"][i1]) - t0
        # the local's timing, stretched if needed so each added stop costs at least the floor
        total = max(times_rel[-1], express_s + MIN_STOP_PENALTY_S * len(run.inserted))
        scale = total / times_rel[-1]
        delta = t0 + total - float(rows["arr_s"][i1])
        before = rows.slice(0, i0 + 1)
        after = rows.slice(i1).with_columns(arr_s=(pl.col("arr_s") + delta).round().cast(pl.Int32),
                                            dep_s=(pl.col("dep_s") + delta).round().cast(pl.Int32))
        middle = pl.DataFrame({
            "trip_id": [trip_id] * len(interior),
            "parent_stop": interior,
            "arr_s": [round(t0 + x * scale) for x in times_rel[:-1]],
            "dep_s": [round(t0 + x * scale) for x in times_rel[:-1]],
        }).with_columns(stop_id=pl.col("parent_stop") + run.direction,
                        direction=pl.lit(run.direction),
                        arr_s=pl.col("arr_s").cast(pl.Int32), dep_s=pl.col("dep_s").cast(pl.Int32))
        merged = pl.concat([before, middle, after], how="diagonal_relaxed")
        merged = merged.with_columns(stop_sequence=pl.int_range(1, merged.height + 1,
                                                                dtype=pl.Int32))
        new_parts.append(merged.select(rows.columns))
        summary.append({"trip_id": trip_id, "added_s": delta})
    feed2 = dict(feed)
    feed2["stop_times"] = pl.concat([keep, *new_parts], how="diagonal_relaxed").select(
        st.columns)
    return feed2, pl.DataFrame(summary)
