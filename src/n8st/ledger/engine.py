"""The scenario ledger: net weighted passenger-hours of a timetable change.

For every origin complex and every departure time (riders arrive at random within each
hour), route the trip on the baseline network and on each scenario network, take the
generalized cost to every destination complex, average over the hour, and weight the
change by the origin-destination flow of that hour:

    net_hours = sum over (o, d, h) of riders[o, d, h] * (cost_scn - cost_base) / 3600

Negative = riders save time overall. Costs are in "in-vehicle seconds":

    cost = in-vehicle + wait_w * (initial + transfer waits) + walk_w * walking
           + transfer_penalty * transfers

Fixed-OD caveat: riders keep today's origin and destination stations. Someone going to
NYU who exits at W 4 St today counts as a W 4 St trip in both worlds, so benefits from
switching to 8 St are not captured here (see docs/methods/ledger.md).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl
from numba import njit, prange

from n8st.routing import raptor
from n8st.routing.network import Network

INF = raptor.INF


@dataclass(frozen=True)
class Weights:
    wait: float = 2.0
    walk: float = 2.0
    transfer_s: float = 300.0

    @property
    def label(self) -> str:
        return f"w{self.wait:g}_k{self.walk:g}_x{self.transfer_s / 60:g}"


BASE = Weights()
GRID = [Weights(w, w, x * 60) for w in (1.5, 2.0, 2.5) for x in (0, 5, 10, 15)] + [
    Weights(2.0, 2.0, 30 * 60)
]


@dataclass
class ComplexIndex:
    """Which routing nodes (platforms) belong to each station complex."""

    ids: np.ndarray  # complex ids, ordered
    node_ptr: np.ndarray  # CSR into nodes
    nodes: np.ndarray

    def position(self) -> dict[int, int]:
        return {int(c): i for i, c in enumerate(self.ids)}

    def nodes_of(self, i: int) -> np.ndarray:
        return self.nodes[self.node_ptr[i]:self.node_ptr[i + 1]]


def complex_index(net: Network, complexes: pl.DataFrame) -> ComplexIndex:
    """complexes: columns complex_id and gtfs_stop_ids (space/comma separated parents)."""
    ids, ptr, nodes = [], [0], []
    for cid, stops in complexes.select("complex_id", "gtfs_stop_ids").iter_rows():
        parents = [s for s in str(stops).replace(",", " ").replace(";", " ").split() if s]
        n = net.nodes_of(parents)
        if len(n) == 0:
            continue
        ids.append(int(float(cid)))
        nodes.extend(n.tolist())
        ptr.append(len(nodes))
    order = np.argsort(ids)
    ids_arr = np.asarray(ids, dtype=np.int64)
    # keep CSR in sorted complex order
    new_ptr, new_nodes = [0], []
    for i in order:
        new_nodes.extend(nodes[ptr[i]:ptr[i + 1]])
        new_ptr.append(len(new_nodes))
    return ComplexIndex(ids_arr[order], np.asarray(new_ptr, np.int64),
                        np.asarray(new_nodes, np.int64))


@njit(cache=True, parallel=True)
def _hourly_costs(arr, wait, ivt, walk, times, hour_of_time, n_hours,
                  c_ptr, c_nodes, w_wait, w_walk, w_xfer, out, out_tt):
    """out[h, d, c] = mean over samples in hour h of min-cost to complex d (weights c).

    out_tt[h, d] = mean earliest-arrival travel time (s). NaN if unreachable in any sample.
    """
    T = arr.shape[0]
    R = arr.shape[1]
    n_c = c_ptr.shape[0] - 1
    n_w = w_wait.shape[0]
    for d in prange(n_c):
        acc = np.zeros((n_hours, n_w))
        acc_tt = np.zeros(n_hours)
        cnt = np.zeros(n_hours)
        bad = np.zeros(n_hours, dtype=np.bool_)
        for ti in range(T):
            h = hour_of_time[ti]
            best_tt = INF
            best = np.full(n_w, np.inf)
            for j in range(c_ptr[d], c_ptr[d + 1]):
                s = c_nodes[j]
                for k in range(1, R):
                    a = arr[ti, k, s]
                    if a >= INF:
                        continue
                    tt = a - times[ti]
                    if tt < best_tt:
                        best_tt = tt
                    for c in range(n_w):
                        cost = (ivt[ti, k, s] + w_wait[c] * wait[ti, k, s]
                                + w_walk[c] * walk[ti, k, s] + w_xfer[c] * (k - 1))
                        if cost < best[c]:
                            best[c] = cost
            if best_tt >= INF:
                bad[h] = True
                continue
            cnt[h] += 1
            acc_tt[h] += best_tt
            for c in range(n_w):
                acc[h, c] += best[c]
        for h in range(n_hours):
            if bad[h] or cnt[h] == 0:
                out_tt[h, d] = np.nan
                for c in range(n_w):
                    out[h, d, c] = np.nan
            else:
                out_tt[h, d] = acc_tt[h] / cnt[h]
                for c in range(n_w):
                    out[h, d, c] = acc[h, c] / cnt[h]


def departure_times(hours: range = range(0, 24),
                    step_s: int = 120) -> tuple[np.ndarray, np.ndarray]:
    times, hour_idx = [], []
    for i, h in enumerate(hours):
        for t in range(h * 3600, (h + 1) * 3600, step_s):
            times.append(t)
            hour_idx.append(i)
    return np.asarray(times, np.int64), np.asarray(hour_idx, np.int64)


def origin_costs(net: Network, cidx: ComplexIndex, origin_pos: int, times: np.ndarray,
                 hour_idx: np.ndarray, n_hours: int, weights: list[Weights],
                 max_rounds: int = 4) -> tuple[np.ndarray, np.ndarray]:
    """Hourly mean generalized cost (and travel time) from one origin complex to every complex.

    Returns (cost[h, d, w], tt[h, d]).
    """
    labels = raptor.profile(net, cidx.nodes_of(origin_pos), times, max_rounds)
    n_c = len(cidx.ids)
    out = np.empty((n_hours, n_c, len(weights)))
    out_tt = np.empty((n_hours, n_c))
    _hourly_costs(labels["arr"], labels["wait"], labels["ivt"], labels["walk"], times, hour_idx,
                  n_hours, cidx.node_ptr, cidx.nodes,
                  np.array([w.wait for w in weights]), np.array([w.walk for w in weights]),
                  np.array([w.transfer_s for w in weights]), out, out_tt)
    return out, out_tt


def run(baseline: Network, scenarios: dict[str, Network], cidx: ComplexIndex,
        od: pl.DataFrame, weights: list[Weights] = GRID, hours: range = range(0, 24),
        step_s: int = 120, progress: bool = True) -> dict[str, pl.DataFrame]:
    """Compute the ledger.

    od: columns origin, destination, hour, riders (weekday average riders per hour).
    Returns:
      pairs   one row per (scenario, origin, destination, hour) with riders > 0 and a
              change: base-weight cost delta (s/rider) and travel-time delta
      totals  one row per (scenario, weights): net, gained and lost passenger-hours
      by_hour one row per (scenario, weights, hour)
    """
    pos = cidx.position()
    od = od.filter(pl.col("origin").is_in(list(pos)) & pl.col("destination").is_in(list(pos))
                   & pl.col("hour").is_in(list(hours)))
    times, hour_idx = departure_times(hours, step_s)
    n_hours = len(hours)
    h_index = {h: i for i, h in enumerate(hours)}
    base_w = next(i for i, w in enumerate(weights) if w == BASE) if BASE in weights else 0

    pair_rows: list[pl.DataFrame] = []
    tot = {(s, wi): [0.0, 0.0, 0.0, 0.0] for s in scenarios for wi in range(len(weights))}
    hourly = {(s, wi): np.zeros(n_hours) for s in scenarios for wi in range(len(weights))}
    origins = od["origin"].unique().sort().to_list()
    for n, o in enumerate(origins):
        rows = od.filter(pl.col("origin") == o)
        d_pos = np.array([pos[d] for d in rows["destination"]])
        h_pos = np.array([h_index[h] for h in rows["hour"]])
        riders = rows["riders"].to_numpy().astype(float)
        base_cost, base_tt = origin_costs(baseline, cidx, pos[o], times, hour_idx, n_hours,
                                          weights)
        for name, net in scenarios.items():
            cost, tt = origin_costs(net, cidx, pos[o], times, hour_idx, n_hours, weights)
            delta = cost[h_pos, d_pos, :] - base_cost[h_pos, d_pos, :]  # (rows, weights)
            ok = np.isfinite(delta).all(axis=1)
            for wi in range(len(weights)):
                dv = delta[ok, wi] * riders[ok] / 3600
                tot[(name, wi)][0] += dv.sum()
                tot[(name, wi)][1] += dv[dv < 0].sum()
                tot[(name, wi)][2] += dv[dv > 0].sum()
                tot[(name, wi)][3] += riders[ok][np.abs(delta[ok, wi]) > 1].sum()
                np.add.at(hourly[(name, wi)], h_pos[ok], dv)
            dtt = tt[h_pos, d_pos] - base_tt[h_pos, d_pos]
            changed = ok & (np.abs(delta[:, base_w]) > 1)
            if changed.any():
                pair_rows.append(pl.DataFrame({
                    "scenario": [name] * int(changed.sum()),
                    "origin": rows["origin"].to_numpy()[changed],
                    "destination": rows["destination"].to_numpy()[changed],
                    "hour": rows["hour"].to_numpy()[changed],
                    "riders": riders[changed],
                    "d_cost_s": delta[changed, base_w],
                    "d_tt_s": dtt[changed],
                    "base_cost_s": base_cost[h_pos, d_pos, base_w][changed],
                }))
        if progress and (n % 50 == 0 or n == len(origins) - 1):
            print(f"  origin {n + 1}/{len(origins)}", flush=True)

    totals = pl.DataFrame([
        {"scenario": s, "weights": weights[wi].label, "wait_w": weights[wi].wait,
         "walk_w": weights[wi].walk, "transfer_min": weights[wi].transfer_s / 60,
         "net_hours": v[0], "hours_saved": -v[1], "hours_lost": v[2], "riders_affected": v[3]}
        for (s, wi), v in tot.items()
    ])
    by_hour = pl.DataFrame([
        {"scenario": s, "weights": weights[wi].label, "hour": hours[i], "net_hours": float(x)}
        for (s, wi), arr in hourly.items() for i, x in enumerate(arr)
    ])
    pairs = pl.concat(pair_rows) if pair_rows else pl.DataFrame()
    return {"pairs": pairs, "totals": totals, "by_hour": by_hour}
