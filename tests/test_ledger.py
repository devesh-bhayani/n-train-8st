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
    times, idx = engine.departure_times(range(7, 9), step_s=600)
    assert list(times) == [25200 + 600 * i for i in range(12)]
    assert list(idx) == [0] * 6 + [1] * 6
