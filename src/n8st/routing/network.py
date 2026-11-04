"""Build a RAPTOR routing network from a GTFS feed (one service day).

Nodes are *platforms* (GTFS child stops such as R20N / R20S), not stations, so that
changing direction (e.g. northbound N -> downtown R at 14 St) costs a platform change
while a same-direction express/local change does not.

Layout (all numpy arrays, CSR-style, ready for numba):

    pattern p: stops  pat_stops[pat_stop_ptr[p]:pat_stop_ptr[p+1]]
               trips  n_trips[p], times in arr/dep at pat_time_ptr[p] + trip*m + i
    stop s:    patterns serving it  stop_pat[stop_pat_ptr[s]:...] with position stop_pos
    stop s:    footpaths  fp_to[fp_ptr[s]:...], fp_dur[...]  (includes platform changes)

A *pattern* is a set of trips with the same stop sequence, ordered so that no trip
overtakes another (required by RAPTOR). Trips that would overtake go to a new pattern.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import polars as pl

# Transfer assumptions (seconds). Documented in docs/methods/router.md.
SAME_DIRECTION_CHANGE_S = 30  # e.g. express <-> local across an island platform
OPPOSITE_DIRECTION_MIN_S = 120  # cross to the other platform; at least this long
DEFAULT_COMPLEX_TRANSFER_S = 180


@dataclass
class Network:
    stop_ids: np.ndarray  # platform id per node (e.g. "R20N")
    parent: np.ndarray  # parent station id per node (e.g. "R20")
    pat_stop_ptr: np.ndarray
    pat_stops: np.ndarray
    pat_time_ptr: np.ndarray
    n_trips: np.ndarray
    arr: np.ndarray
    dep: np.ndarray
    pat_route: np.ndarray  # route_id per pattern
    pat_trip_ids: list[np.ndarray]  # trip_ids per pattern, in pattern order
    stop_pat_ptr: np.ndarray
    stop_pat: np.ndarray
    stop_pos: np.ndarray
    fp_ptr: np.ndarray
    fp_to: np.ndarray
    fp_dur: np.ndarray
    service_id: str = ""
    index: dict[str, int] = field(default_factory=dict)

    @property
    def n_stops(self) -> int:
        return len(self.stop_ids)

    @property
    def n_patterns(self) -> int:
        return len(self.n_trips)

    def nodes_of(self, parents: list[str]) -> np.ndarray:
        """All platform nodes belonging to the given parent stations."""
        want = set(parents)
        return np.array([i for i, p in enumerate(self.parent) if p in want], dtype=np.int64)


def _split_fifo(times: list[tuple[np.ndarray, np.ndarray, str]]) -> list[list[int]]:
    """Group trips (already sorted by first departure) into non-overtaking chains."""
    chains: list[list[int]] = []
    last: list[np.ndarray] = []
    for idx, (_, dep, _) in enumerate(times):
        for c, prev in enumerate(last):
            if np.all(dep >= prev):
                chains[c].append(idx)
                last[c] = dep
                break
        else:
            chains.append([idx])
            last.append(dep)
    return chains


def build(
    stop_times: pl.DataFrame,
    trips: pl.DataFrame,
    transfers: pl.DataFrame | None,
    service_id: str,
    same_direction_s: int = SAME_DIRECTION_CHANGE_S,
    opposite_min_s: int = OPPOSITE_DIRECTION_MIN_S,
) -> Network:
    """stop_times needs trip_id, stop_id, stop_sequence, arr_s, dep_s (see n8st.data.gtfs.load)."""
    tr = trips.filter(pl.col("service_id") == service_id).select("trip_id", "route_id")
    st = (
        stop_times.join(tr, on="trip_id", how="inner")
        .select("trip_id", "route_id", "stop_id", "stop_sequence", "arr_s", "dep_s")
        .sort("trip_id", "stop_sequence")
    )
    stop_ids = np.array(sorted(st["stop_id"].unique().to_list()))
    index = {s: i for i, s in enumerate(stop_ids)}
    parent = np.array([s[:-1] if s[-1] in "NS" else s for s in stop_ids])

    # Group trips by (route, stop sequence).
    by_trip = st.group_by("trip_id", maintain_order=True).agg(
        "route_id", "stop_id", "arr_s", "dep_s"
    )
    groups: dict[tuple, list[tuple[np.ndarray, np.ndarray, str]]] = {}
    for trip_id, route, stops, arr, dep in by_trip.iter_rows():
        key = (route[0], tuple(stops))
        groups.setdefault(key, []).append(
            (np.asarray(arr, dtype=np.int64), np.asarray(dep, dtype=np.int64), trip_id)
        )

    pat_stop_ptr, pat_stops, pat_time_ptr, n_trips = [0], [], [0], []
    arr_flat, dep_flat, pat_route, pat_trip_ids = [], [], [], []
    for (route, stops), trip_list in groups.items():
        trip_list.sort(key=lambda t: (t[1][0], t[0][-1]))
        for chain in _split_fifo(trip_list):
            m = len(stops)
            pat_stops.extend(index[s] for s in stops)
            pat_stop_ptr.append(len(pat_stops))
            for t in chain:
                arr_flat.append(trip_list[t][0])
                dep_flat.append(trip_list[t][1])
            n_trips.append(len(chain))
            pat_time_ptr.append(pat_time_ptr[-1] + m * len(chain))
            pat_route.append(route)
            pat_trip_ids.append(np.array([trip_list[t][2] for t in chain]))

    n_stops = len(stop_ids)
    # stop -> (pattern, position)
    serving: list[list[tuple[int, int]]] = [[] for _ in range(n_stops)]
    for p in range(len(n_trips)):
        for pos, s in enumerate(pat_stops[pat_stop_ptr[p]:pat_stop_ptr[p + 1]]):
            serving[s].append((p, pos))
    stop_pat_ptr = np.zeros(n_stops + 1, dtype=np.int64)
    stop_pat, stop_pos = [], []
    for s in range(n_stops):
        for p, pos in serving[s]:
            stop_pat.append(p)
            stop_pos.append(pos)
        stop_pat_ptr[s + 1] = len(stop_pat)

    fp = _footpaths(stop_ids, parent, index, transfers, same_direction_s, opposite_min_s)
    fp_ptr = np.zeros(n_stops + 1, dtype=np.int64)
    fp_to, fp_dur = [], []
    for s in range(n_stops):
        for q, d in sorted(fp.get(s, {}).items()):
            fp_to.append(q)
            fp_dur.append(d)
        fp_ptr[s + 1] = len(fp_to)

    return Network(
        stop_ids=stop_ids,
        parent=parent,
        pat_stop_ptr=np.asarray(pat_stop_ptr, dtype=np.int64),
        pat_stops=np.asarray(pat_stops, dtype=np.int64),
        pat_time_ptr=np.asarray(pat_time_ptr, dtype=np.int64),
        n_trips=np.asarray(n_trips, dtype=np.int64),
        arr=np.concatenate(arr_flat).astype(np.int64) if arr_flat else np.zeros(0, np.int64),
        dep=np.concatenate(dep_flat).astype(np.int64) if dep_flat else np.zeros(0, np.int64),
        pat_route=np.asarray(pat_route),
        pat_trip_ids=pat_trip_ids,
        stop_pat_ptr=stop_pat_ptr,
        stop_pat=np.asarray(stop_pat, dtype=np.int64),
        stop_pos=np.asarray(stop_pos, dtype=np.int64),
        fp_ptr=fp_ptr,
        fp_to=np.asarray(fp_to, dtype=np.int64),
        fp_dur=np.asarray(fp_dur, dtype=np.int64),
        service_id=service_id,
        index=index,
    )


def _footpaths(stop_ids, parent, index, transfers, same_dir, opp_min):
    """Platform-to-platform transfer times.

    - same platform (change trains, same direction): `same_dir`
    - other platform of the same station: max(MTA self-transfer time, `opp_min`)
    - platforms of another station in the complex: MTA min_transfer_time
    """
    by_parent: dict[str, list[int]] = {}
    for i, p in enumerate(parent):
        by_parent.setdefault(p, []).append(i)
    self_time: dict[str, int] = {}
    inter: dict[tuple[str, str], int] = {}
    if transfers is not None:
        for row in transfers.iter_rows(named=True):
            a, b = row["from_stop_id"], row["to_stop_id"]
            t = row.get("min_transfer_time")
            t = int(t) if t not in (None, "") else DEFAULT_COMPLEX_TRANSFER_S
            if a == b:
                self_time[a] = t
            else:
                inter[(a, b)] = t
    fp: dict[int, dict[int, int]] = {}

    def add(a: int, b: int, d: int) -> None:
        cur = fp.setdefault(a, {})
        if b not in cur or d < cur[b]:
            cur[b] = d

    for p, nodes in by_parent.items():
        for a in nodes:
            add(a, a, same_dir)
            for b in nodes:
                if a != b:
                    add(a, b, max(self_time.get(p, opp_min), opp_min))
    for (pa, pb), t in inter.items():
        for a in by_parent.get(pa, []):
            for b in by_parent.get(pb, []):
                add(a, b, t)
    return fp


def from_feed(feed: dict[str, pl.DataFrame], service_id: str = "Weekday", **kw) -> Network:
    return build(feed["stop_times"], feed["trips"], feed.get("transfers"), service_id, **kw)
