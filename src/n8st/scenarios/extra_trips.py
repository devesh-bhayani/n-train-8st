"""V6: no pattern change, just more of an existing service.

Today two weekday W trips start on the Sea Beach line (86 St 07:04 and 16:33), run up
4th Av, through the Montague tunnel and up the Broadway local, so they are a one-seat
ride from 18 Av to 8 St-NYU (45.5 min). One W runs the other way in the evening
(8 St 21:06). V6 clones those trips at nearby times: more one-seat rides, nobody slowed.

What the ledger can't see: each extra trip needs a train and crew, and slots on the Sea
Beach line, 4th Av, the Montague tunnel and the Broadway local. So V6 is reported as
rider-hours saved *per added trip*, a number to set against those operating costs.
"""

from __future__ import annotations

import polars as pl

SEA_BEACH_STOP = "N05"  # 18 Av (N)
CAMPUS_STOP = "R21"  # 8 St-NYU

# Northbound clones of the 07:04 trip (minutes relative to it): 06:40 ... 07:28 every 12 min.
AM_SHIFTS_MIN = (-24, -12, 12, 24)
# Southbound clones of the 21:06 trip, timed to leave 8 St at these times (seconds).
PM_CAMPUS_DEPARTURES_S = (16 * 3600 + 48 * 60, 17 * 3600 + 12 * 60, 17 * 3600 + 36 * 60,
                          18 * 3600)


def sea_beach_w_trips(feed: dict[str, pl.DataFrame], service_id: str = "Weekday"
                      ) -> pl.DataFrame:
    """Weekday W trips that serve 18 Av: trip_id, direction, first departure, 8 St time."""
    tr = feed["trips"].filter((pl.col("route_id") == "W")
                              & (pl.col("service_id") == service_id)).select("trip_id")
    st = feed["stop_times"].join(tr, on="trip_id")
    ids = st.filter(pl.col("parent_stop") == SEA_BEACH_STOP)["trip_id"].unique()
    st = st.filter(pl.col("trip_id").is_in(ids.to_list()))
    first = st.group_by("trip_id").agg(direction=pl.col("direction").first(),
                                       first_dep_s=pl.col("dep_s").min())
    campus = st.filter(pl.col("parent_stop") == CAMPUS_STOP).select(
        "trip_id", campus_dep_s=pl.col("dep_s"))
    return first.join(campus, on="trip_id", how="left").sort("first_dep_s")


def clone(feed: dict[str, pl.DataFrame], trip_id: str, shifts_s: list[int],
          tag: str = "v6") -> tuple[dict[str, pl.DataFrame], list[str]]:
    """Add copies of trip_id shifted by each of shifts_s seconds."""
    st = feed["stop_times"].filter(pl.col("trip_id") == trip_id)
    tr = feed["trips"].filter(pl.col("trip_id") == trip_id)
    new_st, new_tr, ids = [], [], []
    for k, d in enumerate(shifts_s):
        nid = f"{trip_id}_{tag}_{k}"
        ids.append(nid)
        new_st.append(st.with_columns(trip_id=pl.lit(nid),
                                      arr_s=pl.col("arr_s") + d, dep_s=pl.col("dep_s") + d))
        new_tr.append(tr.with_columns(trip_id=pl.lit(nid)))
    f2 = dict(feed)
    f2["stop_times"] = pl.concat([feed["stop_times"], *new_st], how="vertical_relaxed")
    f2["trips"] = pl.concat([feed["trips"], *new_tr], how="vertical_relaxed")
    return f2, ids


def apply_v6(feed: dict[str, pl.DataFrame], am_shifts_min=AM_SHIFTS_MIN,
             pm_campus_departures_s=PM_CAMPUS_DEPARTURES_S
             ) -> tuple[dict[str, pl.DataFrame], pl.DataFrame]:
    """Return (feed with extra Sea Beach W trips, one row per added trip)."""
    w = sea_beach_w_trips(feed)
    north = w.filter(pl.col("direction") == "N").sort("first_dep_s")
    south = w.filter(pl.col("direction") == "S").sort("first_dep_s")
    rows = []
    f2 = feed
    if north.height:
        am = north.row(0, named=True)  # the morning trip
        f2, ids = clone(f2, am["trip_id"], [m * 60 for m in am_shifts_min], "v6am")
        rows += [{"trip_id": i, "direction": "N",
                  "campus_s": am["campus_dep_s"] + m * 60} for i, m in zip(
                      ids, am_shifts_min, strict=True)]
    if south.height:
        pm = south.row(-1, named=True)
        shifts = [t - pm["campus_dep_s"] for t in pm_campus_departures_s]
        f2, ids = clone(f2, pm["trip_id"], shifts, "v6pm")
        rows += [{"trip_id": i, "direction": "S", "campus_s": t} for i, t in zip(
            ids, pm_campus_departures_s, strict=True)]
    return f2, pl.DataFrame(rows)
