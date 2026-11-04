from pathlib import Path

import numpy as np
import polars as pl
import pytest

from n8st.routing import network, raptor

GTFS = Path(__file__).resolve().parents[1] / "data" / "raw" / "gtfs" / "subway_latest.zip"


def toy():
    """Route X: A -> B -> C (northbound). Route Y: B -> D. Route Z runs the other way at B."""
    rows = [
        # trip, route, stop, seq, arr, dep
        ("x1", "X", "AN", 1, 100, 100),
        ("x1", "X", "BN", 2, 200, 200),
        ("x1", "X", "CN", 3, 300, 300),
        ("x2", "X", "AN", 1, 400, 400),
        ("x2", "X", "BN", 2, 500, 500),
        ("x2", "X", "CN", 3, 600, 600),
        ("y1", "Y", "BN", 1, 220, 220),
        ("y1", "Y", "DN", 2, 320, 320),
        ("y2", "Y", "BN", 1, 260, 260),
        ("y2", "Y", "DN", 2, 360, 360),
        ("z1", "Z", "BS", 1, 300, 300),
        ("z1", "Z", "ES", 2, 350, 350),
        ("z2", "Z", "BS", 1, 340, 340),
        ("z2", "Z", "ES", 2, 390, 390),
    ]
    st = pl.DataFrame(
        rows,
        schema=["trip_id", "route_id", "stop_id", "stop_sequence", "arr_s", "dep_s"],
        orient="row",
    )
    trips = st.select("trip_id", "route_id").unique().with_columns(service_id=pl.lit("Weekday"))
    transfers = pl.DataFrame(
        {"from_stop_id": ["B"], "to_stop_id": ["B"], "min_transfer_time": ["0"]}
    )
    return network.build(st.drop("route_id"), trips, transfers, "Weekday")


def test_transfer_respects_same_direction_change_time():
    net = toy()
    res = raptor.query(net, [net.index["AN"]], t0=0)
    d = net.index["DN"]
    # x1 reaches B at 200; +30 s change misses y1 (220) and catches y2 (260) -> D at 360.
    assert res["arr"][2, d] == 360
    assert res["arr"][1, d] >= raptor.INF  # unreachable with one train
    assert res["wait"][2, d] == 100 + 30
    assert res["ivt"][2, d] == 100 + 100
    assert res["walk"][2, d] == 30


def test_opposite_direction_change_takes_longer():
    net = toy()
    res = raptor.query(net, [net.index["AN"]], t0=0)
    # x1 at BN 200, platform change to BS = max(MTA 0, 120) = 120 -> board at 320 -> z2 (340)
    assert res["arr"][2, net.index["ES"]] == 390


def test_generalized_cost_prefers_fewer_transfers_when_penalised():
    net = toy()
    res = raptor.query(net, [net.index["AN"]], t0=0)
    c = net.index["CN"]
    cost = raptor.generalized_cost(res, 0, wait_w=2, walk_w=2, transfer_penalty_s=300)
    # direct x1: wait 100, ivt 200 -> 2*100 + 200 = 400
    assert cost[c] == pytest.approx(400)


def test_profile_matches_single_queries():
    net = toy()
    times = np.array([0, 150, 350])
    prof = raptor.profile(net, [net.index["AN"]], times)
    for i, t in enumerate(times):
        single = raptor.query(net, [net.index["AN"]], t0=int(t))
        assert np.array_equal(prof["arr"][i], single["arr"])


def test_overtaking_trips_are_split_into_separate_patterns():
    rows = [
        ("a", "AN", 1, 0, 0),
        ("a", "BN", 2, 500, 500),
        ("b", "AN", 1, 100, 100),
        ("b", "BN", 2, 300, 300),  # b leaves later, arrives earlier
    ]
    st = pl.DataFrame(
        rows, schema=["trip_id", "stop_id", "stop_sequence", "arr_s", "dep_s"], orient="row"
    )
    trips = pl.DataFrame(
        {"trip_id": ["a", "b"], "route_id": ["X", "X"], "service_id": ["Weekday"] * 2}
    )
    net = network.build(st, trips, None, "Weekday")
    assert net.n_patterns == 2
    res = raptor.query(net, [net.index["AN"]], t0=0)
    assert res["arr"][1, net.index["BN"]] == 300


@pytest.mark.skipif(not GTFS.exists(), reason="run `make gtfs` first")
def test_mta_18_av_to_union_square_morning():
    from n8st.data import gtfs

    net = network.from_feed(gtfs.load(GTFS), "Weekday")
    t0 = 8 * 3600
    res = raptor.query(net, net.nodes_of(["N05"]), t0)
    tt = raptor.travel_time(res, t0)
    union_sq = net.nodes_of(["R20"])
    minutes = tt[union_sq].min() / 60
    # Scheduled N: ~34 min in the train plus a wait of up to one headway.
    assert 34 <= minutes <= 45
