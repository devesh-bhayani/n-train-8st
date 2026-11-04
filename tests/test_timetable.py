from pathlib import Path

import polars as pl
import pytest

from n8st.data import gtfs
from n8st.scenarios import timetable as tt

GTFS = Path(__file__).resolve().parents[1] / "data" / "raw" / "gtfs" / "subway_latest.zip"
pytestmark = pytest.mark.skipif(not GTFS.exists(), reason="run `make gtfs` first")


@pytest.fixture(scope="module")
def feed():
    return gtfs.load(GTFS)


def times_at(st, trip_id, parents):
    rows = st.filter(pl.col("trip_id") == trip_id)
    return {p: rows.filter(pl.col("parent_stop") == p)["arr_s"][0] for p in parents}


def test_v2_keeps_the_express_leg_to_14_st(feed):
    sc = tt.Scenario("v2", insert=("R21", "R22"), timing="penalty", penalty_s=55)
    f2, summ = tt.apply(feed, sc)
    tid = summ.filter(pl.col("direction") == "S")["trip_id"][0]
    before = times_at(feed["stop_times"], tid, ["R17", "R20", "Q01"])
    after = times_at(f2["stop_times"], tid, ["R17", "R20", "R21", "R22", "Q01"])
    assert after["R20"] - after["R17"] == before["R20"] - before["R17"]
    assert after["Q01"] - before["Q01"] == pytest.approx(110, abs=1)


def test_v1_adds_its_total_and_keeps_times_increasing(feed):
    sc = tt.Scenario("v1", timing="penalty", added_by_direction={"S": 185, "N": 110})
    f2, summ = tt.apply(feed, sc)
    assert set(summ.group_by("direction").agg(pl.col("added_s").median()).rows()) == {
        ("S", 185.0), ("N", 110.0)}
    tid = summ["trip_id"][0]
    seq = f2["stop_times"].filter(pl.col("trip_id") == tid).sort("stop_sequence")
    assert (seq["arr_s"].diff().drop_nulls() >= 0).all()
    assert {"R18", "R19", "R21", "R22"} <= set(seq["parent_stop"].to_list())


def test_other_routes_untouched_without_knock_on(feed):
    sc = tt.Scenario("v1", timing="penalty", penalty_s=50)
    f2, _ = tt.apply(feed, sc)
    r_trips = feed["trips"].filter(pl.col("route_id") == "R")["trip_id"].head(50).to_list()
    a = feed["stop_times"].filter(pl.col("trip_id").is_in(r_trips)).sort("trip_id", "stop_sequence")
    b = f2["stop_times"].filter(pl.col("trip_id").is_in(r_trips)).sort("trip_id", "stop_sequence")
    assert a["arr_s"].to_list() == b["arr_s"].to_list()
