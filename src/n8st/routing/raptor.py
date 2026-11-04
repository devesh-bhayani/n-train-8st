"""RAPTOR (Delling, Pajor & Werneck 2012) in numba, with journey components.

For a rider who appears at origin platforms at time t0, round k finds the earliest
arrival at every platform using at most k trains. Besides arrival time, each label
carries where the time went, so generalized costs can be computed afterwards:

    wait  time on platforms (initial wait + transfer waits)
    ivt   in-vehicle time
    walk  platform changes and walking transfers

Round k labels are "best with <= k trains"; a label is only improved if it beats every
earlier round, so the per-round labels form the Pareto front of (arrival, transfers).
"""

from __future__ import annotations

import numpy as np
from numba import njit, prange

from n8st.routing.network import Network

INF = np.int64(1 << 40)


@njit(cache=True)
def _first_trip(dep, base, m, nt, i, t_min):
    """Index of the first trip departing position i at or after t_min (dep is FIFO-sorted)."""
    lo, hi = 0, nt
    while lo < hi:
        mid = (lo + hi) // 2
        if dep[base + mid * m + i] < t_min:
            lo = mid + 1
        else:
            hi = mid
    return lo


@njit(cache=True)
def _raptor(pat_stop_ptr, pat_stops, pat_time_ptr, n_trips, arr, dep,
            stop_pat_ptr, stop_pat, stop_pos, fp_ptr, fp_to, fp_dur,
            n_stops, origins, t0, max_rounds,
            out_arr, out_wait, out_ivt, out_walk):
    """Fills out_* arrays of shape (max_rounds + 1, n_stops) with arrival labels."""
    n_pat = n_trips.shape[0]
    K = max_rounds
    b_time = np.full((K + 1, n_stops), INF, dtype=np.int64)
    b_wait = np.zeros((K + 1, n_stops), dtype=np.int64)
    b_ivt = np.zeros((K + 1, n_stops), dtype=np.int64)
    b_walk = np.zeros((K + 1, n_stops), dtype=np.int64)
    out_arr[:, :] = INF
    out_wait[:, :] = 0
    out_ivt[:, :] = 0
    out_walk[:, :] = 0
    best = np.full(n_stops, INF, dtype=np.int64)
    marked = np.zeros(n_stops, dtype=np.bool_)
    improved = np.zeros(n_stops, dtype=np.bool_)
    q_pos = np.full(n_pat, -1, dtype=np.int64)

    for o in origins:
        b_time[0, o] = t0
        marked[o] = True

    for k in range(1, K + 1):
        b_time[k, :] = b_time[k - 1, :]
        b_wait[k, :] = b_wait[k - 1, :]
        b_ivt[k, :] = b_ivt[k - 1, :]
        b_walk[k, :] = b_walk[k - 1, :]
        out_arr[k, :] = out_arr[k - 1, :]
        out_wait[k, :] = out_wait[k - 1, :]
        out_ivt[k, :] = out_ivt[k - 1, :]
        out_walk[k, :] = out_walk[k - 1, :]

        q_pos[:] = -1
        any_route = False
        for s in range(n_stops):
            if marked[s]:
                for j in range(stop_pat_ptr[s], stop_pat_ptr[s + 1]):
                    p = stop_pat[j]
                    pos = stop_pos[j]
                    if q_pos[p] == -1 or pos < q_pos[p]:
                        q_pos[p] = pos
                        any_route = True
        if not any_route:
            break
        marked[:] = False
        improved[:] = False

        for p in range(n_pat):
            i0 = q_pos[p]
            if i0 < 0:
                continue
            sp = pat_stop_ptr[p]
            m = pat_stop_ptr[p + 1] - sp
            base = pat_time_ptr[p]
            nt = n_trips[p]
            t = -1
            bstop = -1
            bpos = -1
            for i in range(i0, m):
                s = pat_stops[sp + i]
                if t >= 0:
                    a = arr[base + t * m + i]
                    if a < best[s]:
                        best[s] = a
                        d_b = dep[base + t * m + bpos]
                        out_arr[k, s] = a
                        out_wait[k, s] = b_wait[k - 1, bstop] + (d_b - b_time[k - 1, bstop])
                        out_ivt[k, s] = b_ivt[k - 1, bstop] + (a - d_b)
                        out_walk[k, s] = b_walk[k - 1, bstop]
                        improved[s] = True
                tb = b_time[k - 1, s]
                if tb < INF and i < m - 1:
                    if t < 0 or tb <= dep[base + t * m + i]:
                        t2 = _first_trip(dep, base, m, nt, i, tb)
                        if t2 < nt and (t < 0 or t2 < t):
                            t = t2
                            bstop = s
                            bpos = i

        # Platform changes and walking transfers from platforms reached this round.
        for s in range(n_stops):
            if improved[s]:
                for j in range(fp_ptr[s], fp_ptr[s + 1]):
                    q = fp_to[j]
                    cand = out_arr[k, s] + fp_dur[j]
                    if cand < b_time[k, q]:
                        b_time[k, q] = cand
                        b_wait[k, q] = out_wait[k, s]
                        b_ivt[k, q] = out_ivt[k, s]
                        b_walk[k, q] = out_walk[k, s] + fp_dur[j]
                        marked[q] = True


@njit(cache=True, parallel=True)
def _profile(pat_stop_ptr, pat_stops, pat_time_ptr, n_trips, arr, dep,
             stop_pat_ptr, stop_pat, stop_pos, fp_ptr, fp_to, fp_dur,
             n_stops, origins, times, max_rounds,
             o_arr, o_wait, o_ivt, o_walk):
    for ti in prange(times.shape[0]):
        _raptor(pat_stop_ptr, pat_stops, pat_time_ptr, n_trips, arr, dep,
                stop_pat_ptr, stop_pat, stop_pos, fp_ptr, fp_to, fp_dur,
                n_stops, origins, times[ti], max_rounds,
                o_arr[ti], o_wait[ti], o_ivt[ti], o_walk[ti])


def _args(net: Network):
    return (net.pat_stop_ptr, net.pat_stops, net.pat_time_ptr, net.n_trips, net.arr, net.dep,
            net.stop_pat_ptr, net.stop_pat, net.stop_pos, net.fp_ptr, net.fp_to, net.fp_dur,
            net.n_stops)


def query(net: Network, origins, t0: int, max_rounds: int = 4) -> dict[str, np.ndarray]:
    """Labels for one departure time. Arrays have shape (max_rounds + 1, n_stops)."""
    shape = (max_rounds + 1, net.n_stops)
    out = {k: np.zeros(shape, dtype=np.int64) for k in ("arr", "wait", "ivt", "walk")}
    _raptor(*_args(net), np.asarray(origins, dtype=np.int64), np.int64(t0), max_rounds,
            out["arr"], out["wait"], out["ivt"], out["walk"])
    return out


def profile(net: Network, origins, times, max_rounds: int = 4) -> dict[str, np.ndarray]:
    """Labels for many departure times (in parallel). Arrays: (n_times, rounds + 1, n_stops)."""
    times = np.asarray(times, dtype=np.int64)
    shape = (len(times), max_rounds + 1, net.n_stops)
    out = {k: np.zeros(shape, dtype=np.int64) for k in ("arr", "wait", "ivt", "walk")}
    _profile(*_args(net), np.asarray(origins, dtype=np.int64), times, max_rounds,
             out["arr"], out["wait"], out["ivt"], out["walk"])
    return out


def generalized_cost(labels: dict[str, np.ndarray], t0, wait_w: float = 2.0,
                     walk_w: float = 2.0, transfer_penalty_s: float = 300.0) -> np.ndarray:
    """Minimum generalized cost over rounds, in seconds of in-vehicle time.

    labels: output of query() or profile(); t0: scalar or array matching the time axis.
    cost = ivt + wait_w * wait + walk_w * walk + penalty * (trains - 1)
    The `wait` component already includes the initial wait from t0.
    Unreachable destinations get +inf.
    """
    arr = labels["arr"]
    rounds = arr.shape[-2]
    trains = np.arange(rounds).reshape((1,) * (arr.ndim - 2) + (rounds, 1))
    cost = (labels["ivt"] + wait_w * labels["wait"] + walk_w * labels["walk"]
            + transfer_penalty_s * np.maximum(trains - 1, 0)).astype(float)
    cost[arr >= INF] = np.inf
    cost[..., 0, :] = np.inf  # round 0 = not yet on a train
    return cost.min(axis=-2)


def travel_time(labels: dict[str, np.ndarray], t0) -> np.ndarray:
    """Earliest arrival minus t0 (seconds), best over rounds."""
    arr = labels["arr"][..., 1:, :].min(axis=-2).astype(float)
    t0 = np.asarray(t0, dtype=float)
    if t0.ndim == 1:
        t0 = t0[:, None]
    tt = arr - t0
    tt[arr >= INF] = np.inf
    return tt
