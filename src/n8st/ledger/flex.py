"""Destination flexibility: riders to and from the NYU area pick the best station.

The fixed-OD ledger keeps every rider's stations. But a student who rides the D to
W 4 St today is really going to *a building*, and might ride the N to 8 St instead if
it stopped there. This module gives riders around campus that choice.

Model (deterministic choice, consistent with today's behaviour):

1. Cover the area around Washington Square with points 60 m apart.
2. For a flow from origin o to area station s in hour h, its riders are going to the
   points for which s is the cheapest station *today*:
       cost(o -> s') + walk_weight × walk(s' -> point)
   (the station they use today is the one that's best for where they're going).
3. In a scenario, each of those points re-picks its cheapest station. The change in
   cost, averaged over the points, is that flow's change per rider.
4. The same works in reverse for trips that start in the area (going home).

If no point has s as its best station (the model can't explain today's choice), the
flow keeps its fixed-OD change, so the adjustment is never larger than it should be.

Riders stay uniform over the points they could be going to; weighting by building
density (NYU buildings, LODES jobs) is the obvious next refinement.
"""

from __future__ import annotations

import math

import numpy as np
import polars as pl

AREA_CENTER = (40.7308, -73.9973)  # Washington Square Park
AREA_STATIONS_RADIUS_M = 1100  # area stations: within this distance of the centre
POINTS_RADIUS_M = 900  # destination points: within this distance of the centre
GRID_M = 60
MAX_WALK_M = 900  # a point is only reachable from stations within this distance
DETOUR = 1.25  # street-network distance / straight-line distance
WALK_MPS = 1.3


def _dist_m(lat1, lon1, lat2, lon2):
    k = math.pi / 180
    x = (np.asarray(lon2) - np.asarray(lon1)) * k * np.cos((np.asarray(lat1) + np.asarray(lat2))
                                                             / 2 * k)
    y = (np.asarray(lat2) - np.asarray(lat1)) * k
    return 6_371_000 * np.sqrt(x * x + y * y)


def area_complexes(stations: pl.DataFrame) -> pl.DataFrame:
    """Station complexes near campus with their coordinates (mean of member stations).

    stations: the MTA stations table (complex_id, gtfs_latitude, gtfs_longitude).
    """
    st = stations.select(
        pl.col("complex_id").cast(pl.Float64).cast(pl.Int64),
        pl.col("gtfs_latitude").cast(pl.Float64).alias("lat"),
        pl.col("gtfs_longitude").cast(pl.Float64).alias("lon"),
    ).group_by("complex_id").agg(pl.col("lat").mean(), pl.col("lon").mean())
    d = _dist_m(AREA_CENTER[0], AREA_CENTER[1], st["lat"].to_numpy(), st["lon"].to_numpy())
    return st.with_columns(dist_m=pl.Series(d)).filter(
        pl.col("dist_m") <= AREA_STATIONS_RADIUS_M).sort("complex_id")


def grid_points(center=AREA_CENTER, radius_m=POINTS_RADIUS_M, step_m=GRID_M):
    lat0, lon0 = center
    dlat = step_m / 111_320
    dlon = step_m / (111_320 * math.cos(math.radians(lat0)))
    n = int(radius_m // step_m)
    lats, lons = [], []
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            lat, lon = lat0 + i * dlat, lon0 + j * dlon
            if _dist_m(lat0, lon0, lat, lon) <= radius_m:
                lats.append(lat)
                lons.append(lon)
    return np.array(lats), np.array(lons)


def walk_seconds(area: pl.DataFrame, lats, lons) -> np.ndarray:
    """(points, stations) walking seconds; inf beyond MAX_WALK_M."""
    d = _dist_m(lats[:, None], lons[:, None], area["lat"].to_numpy()[None, :],
                area["lon"].to_numpy()[None, :]) * DETOUR
    w = d / WALK_MPS
    w[d > MAX_WALK_M * DETOUR] = np.inf
    return w


def station_changes(c_base: np.ndarray, c_scn: np.ndarray, walk: np.ndarray,
                    walk_w: float) -> np.ndarray:
    """Mean change in cost, per area station k, for riders whose best station today is k.

    c_base, c_scn: (stations,) transit costs to (or from) each area station (NaN/inf =
    unreachable). walk: (points, stations) seconds. Returns (stations,) with NaN where
    no point picks that station today.
    """
    cb = np.where(np.isfinite(c_base), c_base, np.inf)
    cs = np.where(np.isfinite(c_scn), c_scn, np.inf)
    tot_b = cb[None, :] + walk_w * walk
    tot_s = cs[None, :] + walk_w * walk
    best_b = tot_b.min(axis=1)
    ok = np.isfinite(best_b)
    choice = np.where(ok, tot_b.argmin(axis=1), -1)
    delta = tot_s.min(axis=1) - best_b
    out = np.full(len(c_base), np.nan)
    for k in range(len(c_base)):
        m = (choice == k) & np.isfinite(delta)
        if m.any():
            out[k] = delta[m].mean()
    return out


def choice_shares(od: pl.DataFrame, flex: dict, area: pl.DataFrame, origins: list[int],
                  scenario: str, weight_index: int, walk_w: float,
                  station: int) -> tuple[float, float]:
    """Predicted share of area-bound riders from `origins` who use `station`, today and in
    the scenario. Riders are spread over destination points as in `adjustments`."""
    lats, lons = grid_points()
    walk = walk_seconds(area, lats, lons)
    area_ids = area["complex_id"].to_list()
    dest = flex["destinations"]
    order = [dest.index(c) for c in area_ids]
    o_idx = {o: i for i, o in enumerate(flex["origins"])}
    h_idx = {h: i for i, h in enumerate(flex["hours"])}
    k_target = area_ids.index(station)
    into = od.filter(pl.col("destination").is_in(area_ids) & pl.col("origin").is_in(origins)
                     & pl.col("origin").is_in(list(o_idx)) & pl.col("hour").is_in(list(h_idx)))
    base_n = scn_n = total = 0.0
    for (o, h), grp in into.group_by("origin", "hour"):
        cb = flex["base"][o_idx[o], h_idx[h], order, weight_index].astype(float)
        cs = flex[scenario][o_idx[o], h_idx[h], order, weight_index].astype(float)
        tot_b = np.where(np.isfinite(cb), cb, np.inf)[None, :] + walk_w * walk
        tot_s = np.where(np.isfinite(cs), cs, np.inf)[None, :] + walk_w * walk
        choice_b, choice_s = tot_b.argmin(axis=1), tot_s.argmin(axis=1)
        for d, r in grp.select("destination", "riders").iter_rows():
            pts = choice_b == area_ids.index(d)
            if not pts.any():
                continue
            total += r
            base_n += r * float((choice_b[pts] == k_target).mean())
            scn_n += r * float((choice_s[pts] == k_target).mean())
    return (100 * base_n / total, 100 * scn_n / total) if total else (float("nan"),) * 2


def adjustments(od: pl.DataFrame, flex: dict, flex_out: dict, area: pl.DataFrame,
                weights_walk: list[float], scenarios: list[str]) -> pl.DataFrame:
    """Change in passenger-hours when area riders may switch stations, vs fixed OD.

    Returns one row per (scenario, weight index): fixed and flexible hours for the
    affected flows, and the adjustment (flexible minus fixed; negative = extra benefit).
    """
    lats, lons = grid_points()
    walk = walk_seconds(area, lats, lons)
    area_ids = area["complex_id"].to_list()
    k_of = {c: i for i, c in enumerate(area_ids)}
    rows = []

    # Trips INTO the area: flex["base"][o, h, k, w]
    dest = flex.get("destinations", [])
    order = [dest.index(c) for c in area_ids] if dest else []
    o_idx = {o: i for i, o in enumerate(flex.get("origins", []))}
    h_idx = {h: i for i, h in enumerate(flex.get("hours", []))}
    into = od.filter(pl.col("destination").is_in(area_ids) & pl.col("origin").is_in(list(o_idx))
                     & pl.col("hour").is_in(list(h_idx)))
    # Trips OUT of the area: flex_out["base"][k_origin, h, d, w]
    out_o = {o: i for i, o in enumerate(flex_out.get("origins", []))}
    cpos = {c: i for i, c in enumerate(flex_out.get("complexes", []))}
    out_order = [out_o[c] for c in area_ids] if out_o else []
    outof = od.filter(pl.col("origin").is_in(area_ids) & pl.col("destination").is_in(list(cpos))
                      & pl.col("hour").is_in(list(h_idx)))

    into_groups = into.group_by("origin", "hour").agg("destination", "riders")
    out_groups = outof.group_by("destination", "hour").agg("origin", "riders")

    for s in scenarios:
        for wi, ww in enumerate(weights_walk):
            fixed = flexible = 0.0
            for o, h, dests, riders in into_groups.iter_rows():
                cb = flex["base"][o_idx[o], h_idx[h], order, wi].astype(float)
                cs = flex[s][o_idx[o], h_idx[h], order, wi].astype(float)
                g = station_changes(cb, cs, walk, ww)
                for d, r in zip(dests, riders, strict=True):
                    k = k_of[d]
                    f = cs[k] - cb[k]
                    if not np.isfinite(f):
                        continue
                    fixed += r * f
                    flexible += r * (g[k] if np.isfinite(g[k]) else f)
            if out_order:
                for d, h, origs, riders in out_groups.iter_rows():
                    cb = flex_out["base"][out_order, h_idx[h], cpos[d], wi].astype(float)
                    cs = flex_out[s][out_order, h_idx[h], cpos[d], wi].astype(float)
                    g = station_changes(cb, cs, walk, ww)
                    for o, r in zip(origs, riders, strict=True):
                        k = k_of[o]
                        f = cs[k] - cb[k]
                        if not np.isfinite(f):
                            continue
                        fixed += r * f
                        flexible += r * (g[k] if np.isfinite(g[k]) else f)
            rows.append({"scenario": s, "weight_index": wi, "fixed_hours": fixed / 3600,
                         "flexible_hours": flexible / 3600,
                         "adjustment_hours": (flexible - fixed) / 3600})
    return pl.DataFrame(rows)
