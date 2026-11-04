"""Counterfactual timetables: make an express service stop at Broadway local stations.

The weekday N runs express between 34 St-Herald Sq (R17) and Canal St's bridge level
(Q01). A scenario inserts local stops into that segment for each affected trip, sets
the new times from a timing model, and shifts everything after the segment by the
extra time, so the rest of the trip runs exactly as before, just later.

Variants (see docs/preregistration.md):
    V1  insert 28 St, 23 St, 8 St, Prince St (today's weekend N pattern)
    V2  insert 8 St and Prince St only (needs a crossover south of 14 St; unverified)
    V3  insert 8 St only (needs that crossover *and* skipping Prince St)
    V4  as V1 but for the Q instead of the N
    V5  V1 only for trips in chosen hours

Timing models:
    "template"  segment times from the weekend local N (the MTA's own local schedule)
    "penalty"   express time + `penalty_s` per inserted stop, spread over the segment
"""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl

SOUTH_SEGMENT = ["R17", "R18", "R19", "R20", "R21", "R22", "Q01"]  # 34 St -> Canal (bridge)
VARIANT_STOPS = {
    "V1": ["R18", "R19", "R21", "R22"],
    "V2": ["R21", "R22"],
    "V3": ["R21"],
}


@dataclass(frozen=True)
class Scenario:
    name: str
    route: str = "N"
    insert: tuple[str, ...] = ("R18", "R19", "R21", "R22")
    timing: str = "template"
    penalty_s: float = 45.0
    hours: tuple[int, ...] | None = None  # departure hour at the segment entry; None = all
    service_id: str = "Weekday"
    # Optional total added seconds per direction (overrides penalty_s per stop), e.g. from
    # the simulation: {"S": 185, "N": 110}.
    added_by_direction: dict | None = None
    # Knock-on effects on other routes: (route, direction, seconds), applied from the
    # corridor exit onward (S: Canal; N: 57 St-7 Av).
    knock_on: tuple[tuple[str, str, float], ...] = ()


CORRIDOR_EXIT = {"S": ("R23", "Q01"), "N": ("R14",)}


def shift_after_corridor(st: pl.DataFrame, trips: pl.DataFrame, route: str, direction: str,
                         seconds: float, service_id: str = "Weekday") -> pl.DataFrame:
    """Delay (or advance) every stop of a route's trips from the corridor exit onward."""
    ids = trips.filter((pl.col("route_id") == route) & (pl.col("service_id") == service_id))[
        "trip_id"].to_list()
    exits = CORRIDOR_EXIT[direction]
    mask = pl.col("trip_id").is_in(ids) & (pl.col("direction") == direction)
    first_exit = (pl.when(pl.col("parent_stop").is_in(list(exits)))
                  .then(pl.col("stop_sequence")).min().over("trip_id"))
    shift = mask & (pl.col("stop_sequence") >= first_exit)
    return st.with_columns(
        arr_s=pl.when(shift).then((pl.col("arr_s") + seconds).round().cast(pl.Int32))
        .otherwise(pl.col("arr_s")),
        dep_s=pl.when(shift).then((pl.col("dep_s") + seconds).round().cast(pl.Int32))
        .otherwise(pl.col("dep_s")),
    )


SCENARIOS = {
    "V1": Scenario("V1"),
    "V2": Scenario("V2", insert=("R21", "R22")),
    "V3": Scenario("V3", insert=("R21",)),
    "V4": Scenario("V4", route="Q"),
    "V5": Scenario("V5", hours=tuple(range(10, 16)) + tuple(range(19, 24))),
}


def segment_template(feed: dict[str, pl.DataFrame], route: str = "N",
                     service_id: str = "Saturday") -> dict[tuple[str, str, str], float]:
    """Median scheduled seconds between consecutive local stations, per direction.

    Uses trips that stop at every station in SOUTH_SEGMENT (the weekend local N).
    Returns {(direction, from_parent, to_parent): seconds}.
    """
    trips = feed["trips"].filter(
        (pl.col("route_id") == route) & (pl.col("service_id") == service_id)
    ).select("trip_id")
    st = (
        feed["stop_times"].join(trips, on="trip_id")
        .filter(pl.col("parent_stop").is_in(SOUTH_SEGMENT))
        .sort("trip_id", "stop_sequence")
    )
    full = st.group_by("trip_id").agg(n=pl.len()).filter(pl.col("n") == len(SOUTH_SEGMENT))
    st = st.join(full.select("trip_id"), on="trip_id")
    seg = st.with_columns(
        nxt=pl.col("parent_stop").shift(-1).over("trip_id"),
        dt=(pl.col("arr_s").shift(-1).over("trip_id") - pl.col("dep_s")),
    ).drop_nulls("nxt")
    med = seg.group_by("direction", "parent_stop", "nxt").agg(pl.col("dt").median())
    out = {(d, a, b): float(t) for d, a, b, t in med.iter_rows()}
    if len(out) < 2 * (len(SOUTH_SEGMENT) - 1):
        raise ValueError(f"template incomplete: found {len(out)} segments for {route}/{service_id}")
    return out


def apply(feed: dict[str, pl.DataFrame], scenario: Scenario,
          template: dict | None = None) -> tuple[dict[str, pl.DataFrame], pl.DataFrame]:
    """Return (new feed, per-trip summary). Only stop_times changes."""
    template = template or segment_template(feed)
    trips = feed["trips"].filter(
        (pl.col("route_id") == scenario.route) & (pl.col("service_id") == scenario.service_id)
    )
    trip_ids = set(trips["trip_id"].to_list())
    st = feed["stop_times"]
    affected = st.filter(pl.col("trip_id").is_in(list(trip_ids)))
    untouched = st.filter(~pl.col("trip_id").is_in(list(trip_ids)))

    new_rows, summary = [], []
    for (trip_id,), rows in affected.sort("stop_sequence").group_by("trip_id",
                                                                     maintain_order=True):
        rows = rows.sort("stop_sequence")
        parents = rows["parent_stop"].to_list()
        direction = rows["direction"][0]
        entry, exit_ = ("R17", "Q01") if direction == "S" else ("Q01", "R17")
        express = (entry in parents and exit_ in parents and "R21" not in parents
                   and parents.index(exit_) > parents.index(entry))
        i_in = parents.index(entry) if express else -1
        t_entry = rows["dep_s"][i_in] if express else None
        hour_ok = express and (scenario.hours is None
                               or (int(t_entry) // 3600) % 24 in scenario.hours)
        if not (express and hour_ok):
            new_rows.append(rows)
            continue

        i_out = parents.index(exit_)
        full = SOUTH_SEGMENT if direction == "S" else SOUTH_SEGMENT[::-1]
        old_mid = parents[i_in + 1:i_out]  # e.g. ["R20"]
        seg_stops = [s for s in full if s in (entry, exit_) or s in old_mid
                     or s in scenario.insert]
        t_exit_old = float(rows["arr_s"][i_out])
        times = _segment_times(direction, seg_stops, float(t_entry), rows, parents,
                               template, scenario)
        delta = times[-1] - t_exit_old

        before = rows.slice(0, i_in + 1)
        after = rows.slice(i_out).with_columns(
            arr_s=(pl.col("arr_s") + delta).round().cast(pl.Int32),
            dep_s=(pl.col("dep_s") + delta).round().cast(pl.Int32),
        )
        middle = pl.DataFrame({
            "trip_id": [trip_id] * (len(seg_stops) - 2),
            "parent_stop": seg_stops[1:-1],
            "arr_s": [round(t) for t in times[1:-1]],
            "dep_s": [round(t) for t in times[1:-1]],
        }).with_columns(
            stop_id=pl.col("parent_stop") + direction,
            direction=pl.lit(direction),
            arr_s=pl.col("arr_s").cast(pl.Int32),
            dep_s=pl.col("dep_s").cast(pl.Int32),
        )
        merged = pl.concat([before, middle, after], how="diagonal_relaxed")
        merged = merged.with_columns(
            stop_sequence=pl.int_range(1, merged.height + 1, dtype=pl.Int32),
        )
        new_rows.append(merged.select(rows.columns))
        summary.append({"trip_id": trip_id, "direction": direction,
                        "entry_time_s": int(t_entry), "added_s": round(delta, 1),
                        "stops_added": len(seg_stops) - 2 - len(old_mid)})

    new_st = pl.concat([untouched, *new_rows], how="diagonal_relaxed").select(st.columns)
    for route, direction, seconds in scenario.knock_on:
        new_st = shift_after_corridor(new_st, feed["trips"], route, direction, seconds,
                                      scenario.service_id)
    feed2 = dict(feed)
    feed2["stop_times"] = new_st
    return feed2, pl.DataFrame(summary)


def _segment_times(direction, seg_stops, t_entry, rows, parents, template, scenario):
    """Times at each stop of the rebuilt segment."""
    full = SOUTH_SEGMENT if direction == "S" else SOUTH_SEGMENT[::-1]
    exit_ = seg_stops[-1]
    t_exit_old = float(rows["arr_s"][parents.index(exit_)])

    def tmpl(a, b):
        ia, ib = full.index(a), full.index(b)
        return sum(template[(direction, full[i], full[i + 1])] for i in range(ia, ib))

    def old(a, b):
        return float(rows["arr_s"][parents.index(b)] - rows["dep_s"][parents.index(a)])

    if scenario.timing == "penalty":
        # Work leg by leg between the trip's original stops: a leg with no inserted
        # stops keeps its own scheduled time (so V2 still reaches 14 St on time); a leg
        # with k inserted stops gets its old time plus its share of the added time,
        # spread over its new hops in proportion to the local template.
        originals = [s for s in seg_stops if s in parents]
        n_added = sum(1 for s in seg_stops[1:-1] if s in scenario.insert)
        added = (scenario.added_by_direction[direction] if scenario.added_by_direction
                 else n_added * scenario.penalty_s)
        times = [t_entry]
        for a, b in zip(originals[:-1], originals[1:], strict=True):
            leg = seg_stops[seg_stops.index(a):seg_stops.index(b) + 1]
            k = len(leg) - 2
            leg_total = old(a, b) + (added * k / n_added if n_added else 0.0)
            shares = [tmpl(x, y) for x, y in zip(leg[:-1], leg[1:], strict=True)]
            for s in shares:
                times.append(times[-1] + s * leg_total / sum(shares))
        return times

    # template timing
    times = [t_entry]
    for a, b in zip(seg_stops[:-1], seg_stops[1:], strict=True):
        if a in parents and b in parents and not any(
                s in scenario.insert for s in full[full.index(a) + 1:full.index(b)]):
            dt = old(a, b)  # an untouched express leg keeps its own schedule
        else:
            skipped = full.index(b) - full.index(a) - 1
            dt = tmpl(a, b) - skipped * scenario.penalty_s
        times.append(times[-1] + dt)
    return times
