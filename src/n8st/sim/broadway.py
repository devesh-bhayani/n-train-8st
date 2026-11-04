"""Discrete-event simulation of the Broadway line, 57 St-7 Av to Canal St (SimPy).

Each train is a SimPy process that moves through signal blocks. A block is a
capacity-1 resource; a train holds the block it is in plus `hold - 1` blocks behind
it, so a follower must stay that far back (a simple model of block signalling).
Crossovers are blocks shared by the two tracks they join, so an N switching from the
local to the express track must find gaps in both streams.

At platforms, dwell = base + per-passenger time x passengers, where passengers build up
at rate lambda while the platform waits for its next train. Long gaps therefore make
long dwells, which make the next gap longer: the bunching feedback that turns small
delays into irregular service.

Trains enter the corridor at the times they were *observed* entering it (subwaydata.nyc),
so each simulated day replays a real day's irregularity. The same entries are used for
the baseline and every scenario (common random numbers), so differences are caused by
the timetable change, not by noise.

Track codes follow the MTA feed: A1/A3 southbound local/express, A2/A4 northbound
local/express, H1/H2 Manhattan Bridge level at Canal, B1/B2 Canal lower level.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

import numpy as np
import simpy

# ----------------------------------------------------------------------------- layout

LOCAL_S = ["R14", "R15", "R16", "R17", "R18", "R19", "R20", "R21", "R22"]
EXPRESS_S = ["R14", "R16", "R17", "R20"]

# (track, station) sequences for each route and scenario, southbound.
PATHS_S = {
    "base": {
        "R": [("A1", s) for s in LOCAL_S] + [("B1", "R23")],
        "W": [("A1", s) for s in LOCAL_S] + [("B1", "R23")],
        "Q": [("A3", s) for s in EXPRESS_S] + [("H1", "Q01")],
        "N": [("A1", "R14"), ("A1", "R15"), ("A1", "R16"), ("A3", "R17"), ("A3", "R20"),
              ("H1", "Q01")],
    },
}
PATHS_S["V1"] = dict(PATHS_S["base"], N=[("A1", s) for s in LOCAL_S] + [("H1", "Q01")])
PATHS_S["V2"] = dict(PATHS_S["base"], N=[("A1", "R14"), ("A1", "R15"), ("A1", "R16"),
                                         ("A3", "R17"), ("A3", "R20"), ("A1", "R21"),
                                         ("A1", "R22"), ("H1", "Q01")])

LOCAL_N = list(reversed(LOCAL_S))
EXPRESS_N = list(reversed(EXPRESS_S))
PATHS_N = {
    "base": {
        "R": [("B2", "R23")] + [("A2", s) for s in LOCAL_N],
        "W": [("B2", "R23")] + [("A2", s) for s in LOCAL_N],
        "Q": [("H2", "Q01")] + [("A4", s) for s in EXPRESS_N],
        "N": [("H2", "Q01"), ("A4", "R20"), ("A4", "R17"), ("A2", "R16"), ("A2", "R15"),
              ("A2", "R14")],
    },
}
PATHS_N["V1"] = dict(PATHS_N["base"], N=[("H2", "Q01")] + [("A2", s) for s in LOCAL_N])
PATHS_N["V2"] = dict(PATHS_N["base"], N=[("H2", "Q01"), ("A2", "R22"), ("A2", "R21"),
                                         ("A4", "R20"), ("A4", "R17"), ("A2", "R16"),
                                         ("A2", "R15"), ("A2", "R14")])
PATHS = {"S": PATHS_S, "N": PATHS_N}

# Physical continuity: the express track becomes the bridge track at Canal, and the
# local track continues to Canal's lower level.
SAME_TRACK = {("A3", "H1"), ("H2", "A4"), ("A1", "B1"), ("B2", "A2")}

# Running times (s) for moves that the observed weekday data can't provide, because
# no weekday train makes them. From observed weekend N trains (crossover at Prince) or,
# for the hypothetical V2 crossover south of 14 St, the local run plus 15 s.
FALLBACK_EDGE_S = {
    ("S", "A1", "R22", "H1", "Q01"): 145,
    ("N", "H2", "Q01", "A2", "R22"): 164,
    ("S", "A3", "R20", "A1", "R21"): 124,
    ("N", "A2", "R21", "A4", "R20"): 124,
}


@dataclass
class Params:
    hold: int = 2  # blocks a train occupies (current + behind)
    block_target_s: float = 35.0  # target block running time
    base_dwell_s: float = 20.0
    per_pax_s: float = 0.04  # seconds of dwell per passenger boarding or alighting
    run_noise_sd: float = 0.04  # lognormal sd of running-time multipliers
    dwell_noise_sd: float = 0.15
    # passengers per second arriving at each platform (both boarding and alighting
    # activity), keyed by station; local and express platforms share the station rate.
    pax_rate: dict[str, float] = field(default_factory=dict)
    default_pax_rate: float = 0.25
    # multiplier on pax_rate by hour of day (1.0 = the peak-hour rate)
    hour_factor: dict[int, float] = field(default_factory=dict)
    pax_scale: float = 1.0  # calibration knob on all passenger rates
    # Occasional long holds (door problems, sick passenger, crew): probability per stop
    # and mean extra seconds (exponential). These make the slow tail of real service.
    incident_prob: float = 0.0
    incident_mean_s: float = 90.0
    max_dwell_s: float = 300.0


@dataclass
class EdgeSpec:
    blocks: list[str]
    run_s: float  # unimpeded running time for the whole edge (excluding dwell)


def _segment_name(track: str, a: str, b: str) -> str:
    return f"{track}:{a}-{b}"


def build_edges(direction: str, scenario: str, stop_to_stop_s: dict, params: Params
                ) -> dict[tuple, EdgeSpec]:
    """Block lists and unimpeded running times for every move in the scenario's paths.

    stop_to_stop_s[(direction, track_a, a, track_b, b)] = observed low-quantile seconds
    from arriving at a to arriving at b (it includes a minimal dwell at a).
    """
    paths = PATHS[direction][scenario]
    # physical segments on each track: consecutive stations of any path on that track
    edges: dict[tuple, EdgeSpec] = {}
    segment_blocks: dict[str, int] = {}

    def nblocks(run: float) -> int:
        return max(2, int(round(run / params.block_target_s)))

    def seg_time(key):
        if key in stop_to_stop_s:
            return stop_to_stop_s[key]
        if key in FALLBACK_EDGE_S:
            return FALLBACK_EDGE_S[key]
        raise KeyError(f"no running time for {key}")

    # First pass: same-track moves define the physical segments and their blocks.
    for route_path in paths.values():
        for (ta, a), (tb, b) in zip(route_path[:-1], route_path[1:], strict=True):
            if ta == tb or (ta, tb) in SAME_TRACK:
                key = (direction, ta, a, tb, b)
                run = max(20.0, seg_time(key) - params.base_dwell_s)
                name = _segment_name(ta, a, b)
                n = segment_blocks.setdefault(name, nblocks(run))
                edges[(ta, a, tb, b)] = EdgeSpec([f"{name}#{i}" for i in range(n)], run)

    # Second pass: crossovers share the first block of the track they leave and the last
    # block of the track they join.
    for route_path in paths.values():
        for (ta, a), (tb, b) in zip(route_path[:-1], route_path[1:], strict=True):
            if ta == tb or (ta, tb) in SAME_TRACK:
                continue
            key = (direction, ta, a, tb, b)
            run = max(20.0, seg_time(key) - params.base_dwell_s)
            leave = _leaving_segment(paths, ta, a)
            join = _joining_segment(paths, tb, b)
            first = f"{leave}#0" if leave else f"X:{ta}:{a}-out"
            last = (f"{join}#{segment_blocks.get(join, 2) - 1}" if join
                    else f"X:{tb}:{b}-in")
            edges[(ta, a, tb, b)] = EdgeSpec([first, f"X:{ta}{tb}:{a}-{b}", last], run)
    return edges


def _leaving_segment(paths, track, station):
    """The same-track segment that starts at (track, station), if any train runs it."""
    for p in paths.values():
        for (ta, a), (tb, b) in zip(p[:-1], p[1:], strict=True):
            if ta == track and a == station and (ta == tb or (ta, tb) in SAME_TRACK):
                return _segment_name(ta, a, b)
    return None


def _joining_segment(paths, track, station):
    """The same-track segment that ends at (track, station), if any train runs it."""
    for p in paths.values():
        for (ta, a), (tb, b) in zip(p[:-1], p[1:], strict=True):
            if tb == track and b == station and (ta == tb or (ta, tb) in SAME_TRACK):
                return _segment_name(ta, a, b)
    return None


# ----------------------------------------------------------------------------- model

@dataclass
class TrainRecord:
    train_id: str
    route: str
    entry_s: float
    stops: list[tuple[str, str, float, float]] = field(default_factory=list)  # track, stn, arr, dep

    @property
    def exit_s(self) -> float:
        return self.stops[-1][2] if self.stops else math.nan


class Corridor:
    def __init__(self, env: simpy.Environment, edges: dict[tuple, EdgeSpec], params: Params,
                 rng: np.random.Generator):
        self.env = env
        self.edges = edges
        self.params = params
        self.rng = rng
        self.blocks: dict[str, simpy.Resource] = {}
        self.last_departure: dict[str, float] = {}  # per station (shared by its platforms)
        self.records: list[TrainRecord] = []

    def block(self, name: str) -> simpy.Resource:
        if name not in self.blocks:
            self.blocks[name] = simpy.Resource(self.env, capacity=1)
        return self.blocks[name]

    def dwell(self, station: str) -> float:
        p = self.params
        hour = int(self.env.now // 3600) % 24
        rate = (p.pax_rate.get(station, p.default_pax_rate) * p.pax_scale
                * p.hour_factor.get(hour, 1.0))
        gap = self.env.now - self.last_departure.get(station, self.env.now - 240.0)
        pax = self.rng.poisson(max(rate * min(gap, 1200.0), 0.0))
        d = (p.base_dwell_s + p.per_pax_s * pax) * self.rng.lognormal(0.0, p.dwell_noise_sd)
        if p.incident_prob and self.rng.random() < p.incident_prob:
            d += self.rng.exponential(p.incident_mean_s)
        return min(d, p.max_dwell_s)

    def train(self, train_id: str, route: str, path: list[tuple[str, str]], entry_s: float):
        env, p = self.env, self.params
        rec = TrainRecord(train_id, route, entry_s)
        self.records.append(rec)
        yield env.timeout(max(0.0, entry_s - env.now))
        held: deque = deque()

        def acquire(name):
            req = self.block(name).request()
            yield req
            held.append((name, req))
            while len(held) > p.hold:
                old_name, old_req = held.popleft()
                self.block(old_name).release(old_req)

        # Enter the first platform.
        t0, s0 = path[0]
        yield from acquire(f"P:{t0}:{s0}")
        for i, (track, station) in enumerate(path):
            arr = env.now
            if i < len(path) - 1:
                yield env.timeout(self.dwell(station))
            dep = env.now
            self.last_departure[station] = dep
            rec.stops.append((track, station, arr, dep))
            if i == len(path) - 1:
                break
            nt, ns = path[i + 1]
            edge = self.edges[(track, station, nt, ns)]
            per_block = edge.run_s / len(edge.blocks)
            mult = self.rng.lognormal(0.0, p.run_noise_sd)
            for b in edge.blocks:
                yield from acquire(b)
                yield env.timeout(per_block * mult)
            yield from acquire(f"P:{nt}:{ns}")
        while held:
            name, req = held.popleft()
            self.block(name).release(req)


def simulate(entries: list[tuple[str, str, float]], direction: str, scenario: str,
             stop_to_stop_s: dict, params: Params, seed: int = 0) -> list[TrainRecord]:
    """entries: (train_id, route, entry time in seconds) at the corridor's first platform."""
    env = simpy.Environment()
    edges = build_edges(direction, scenario, stop_to_stop_s, params)
    corridor = Corridor(env, edges, params, np.random.default_rng(seed))
    paths = PATHS[direction][scenario]
    for train_id, route, t in sorted(entries, key=lambda e: e[2]):
        if route in paths:
            env.process(corridor.train(train_id, route, paths[route], t))
    env.run()
    return corridor.records
