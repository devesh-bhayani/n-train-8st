import polars as pl
import pytest

from n8st.ledger import engine
from n8st.routing import network


def line(delay_at_c: int = 0) -> network.Network:
    """Trains A -> B -> C every 5 minutes for two hours; optionally slower into C."""
    rows = []
    for i, t in enumerate(range(0, 7800, 300)):
        rows += [(f"t{i}", "AN", 1, t, t), (f"t{i}", "BN", 2, t + 120, t + 120),
                 (f"t{i}", "CN", 3, t + 240 + delay_at_c, t + 240 + delay_at_c)]
    st = pl.DataFrame(rows, schema=["trip_id", "stop_id", "stop_sequence", "arr_s", "dep_s"],
                      orient="row")
    trips = st.select("trip_id").unique().with_columns(route_id=pl.lit("X"),
                                                       service_id=pl.lit("Weekday"))
    return network.build(st, trips, None, "Weekday")


COMPLEXES = pl.DataFrame({"complex_id": [1, 2, 3], "gtfs_stop_ids": ["A", "B", "C"]})


def test_slower_trains_cost_exactly_riders_times_delay():
    base, slow = line(), line(delay_at_c=60)
    cidx = engine.complex_index(base, COMPLEXES)
    od = pl.DataFrame({"origin": [1, 1], "destination": [3, 2], "hour": [0, 0],
                       "riders": [10.0, 5.0]})
    out = engine.run(base, {"slow": slow}, cidx, od, hours=range(0, 1), progress=False)
    totals = out["totals"]
    # Only A->C riders are delayed, by 60 s each, whatever the weights.
    assert totals["net_hours"].to_list() == pytest.approx([10 * 60 / 3600] * len(engine.GRID))
    pairs = out["pairs"]
    assert pairs.height == 1 and pairs["destination"].item() == 3
    assert pairs["d_tt_s"].item() == pytest.approx(60)


def test_complex_index_maps_platforms():
    net = line()
    cidx = engine.complex_index(net, COMPLEXES)
    assert list(cidx.ids) == [1, 2, 3]
    assert [net.stop_ids[n] for n in cidx.nodes_of(cidx.position()[2])] == ["BN"]


def test_departure_times_cover_each_hour_evenly():
    times, idx = engine.departure_times(range(7, 9), step_s=600, jitter_seed=None)
    assert list(times) == [25200 + 600 * i for i in range(12)]
    assert list(idx) == [0] * 6 + [1] * 6


def test_jittered_times_stay_inside_their_windows_and_are_reproducible():
    a, idx = engine.departure_times(range(7, 9), step_s=600, jitter_seed=3)
    b, _ = engine.departure_times(range(7, 9), step_s=600, jitter_seed=3)
    assert list(a) == list(b)
    for k, t in enumerate(a):
        assert 25200 + 600 * k <= t < 25200 + 600 * (k + 1)


def test_uniform_shift_of_a_line_costs_nothing_on_average():
    """The bug this guards against: grid-aligned sampling made pure phase shifts look
    costly. With jittered arrivals and many samples, shifting every train by 20 s should
    change the average wait by ~0."""
    base, shifted = line(), line(delay_at_c=0)
    # shift the whole line by 20 s: rebuild with offset trips
    rows = []
    for i, t in enumerate(range(20, 7820, 300)):
        rows += [(f"t{i}", "AN", 1, t, t), (f"t{i}", "BN", 2, t + 120, t + 120),
                 (f"t{i}", "CN", 3, t + 240, t + 240)]
    st = pl.DataFrame(rows, schema=["trip_id", "stop_id", "stop_sequence", "arr_s", "dep_s"],
                      orient="row")
    trips = st.select("trip_id").unique().with_columns(route_id=pl.lit("X"),
                                                       service_id=pl.lit("Weekday"))
    shifted = network.build(st, trips, None, "Weekday")
    cidx = engine.complex_index(base, COMPLEXES)
    od = pl.DataFrame({"origin": [1], "destination": [3], "hour": [0], "riders": [100.0]})
    out = engine.run(base, {"shift": shifted}, cidx, od, hours=range(0, 1), step_s=10,
                     progress=False)
    net = out["totals"].filter(pl.col("weights") == engine.BASE.label)["net_hours"].item()
    assert abs(net) < 0.2  # vs 100 riders x 20 s x 2 = 1.1 h with grid-aligned sampling


def test_flex_station_changes_lets_riders_switch():
    import numpy as np

    from n8st.ledger.flex import station_changes

    # Two stations, three points: point 0 next to station 0, point 2 next to station 1,
    # point 1 halfway. Walking seconds:
    walk = np.array([[0.0, 600.0], [300.0, 300.0], [600.0, 0.0]])
    base = np.array([1000.0, 1300.0])  # station 0 is cheaper to reach today
    scn = np.array([1000.0, 700.0])  # the scenario makes station 1 much cheaper
    g = station_changes(base, scn, walk, walk_w=1.0)
    # Today points 0 and 1 use station 0 (cost 1000, 1300); point 2 uses station 1 (1300).
    # In the scenario: point 0 stays (1000 -> 1000), point 1 switches (1300 -> 1000),
    # point 2 stays (1300 -> 700).
    assert g[0] == pytest.approx((0 + -300) / 2)
    assert g[1] == pytest.approx(-600)


def two_routes(x_offset: int = 0) -> network.Network:
    """Route X runs A -> B and route Y runs B -> D, both every 5 minutes. Y leaves B at
    :02:30 past each 5 minutes; X is shifted by x_offset, which sets the wait at B."""
    rows = []
    for i, t in enumerate(range(0, 7800, 300)):
        a = t + x_offset
        rows += [(f"x{i}", "AN", 1, a, a), (f"x{i}", "BN", 2, a + 120, a + 120)]
        b = t + 150
        rows += [(f"y{i}", "BN", 1, b, b), (f"y{i}", "DN", 2, b + 120, b + 120)]
    st = pl.DataFrame(rows, schema=["trip_id", "stop_id", "stop_sequence", "arr_s", "dep_s"],
                      orient="row")
    trips = st.select("trip_id").unique().with_columns(
        route_id=pl.col("trip_id").str.slice(0, 1).str.to_uppercase(),
        service_id=pl.lit("Weekday"))
    return network.build(st, trips, None, "Weekday")


def test_phase_averaging_cancels_a_pure_shift():
    """What n8st.ledger.phase_avg relies on. Shifting route X by 60 s with nothing else
    changed moves the A -> D transfer wait a lot on any one timetable, but averaged over
    offsets covering a whole headway (applied to baseline and scenario alike) the
    'effect' is exactly zero: the scenario's phases are the baseline's, relabelled."""
    complexes = pl.DataFrame({"complex_id": [1, 2, 4], "gtfs_stop_ids": ["A", "B", "D"]})
    od = pl.DataFrame({"origin": [1], "destination": [4], "hour": [1], "riders": [100.0]})
    cidx = engine.complex_index(two_routes(), complexes)
    nets = []
    for phi in range(0, 300, 60):
        out = engine.run(two_routes(phi), {"shift": two_routes(phi + 60)}, cidx, od,
                         weights=[engine.BASE], hours=range(1, 2), step_s=10,
                         progress=False)
        nets.append(out["totals"]["net_hours"].item())
    assert max(abs(n) for n in nets) > 1.0  # any single alignment is far from zero
    assert abs(sum(nets) / len(nets)) < 1e-6
