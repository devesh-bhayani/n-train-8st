from datetime import UTC, datetime, timedelta

import polars as pl
import pytest

from n8st.shuttle.headways import headway_summary, headways, stop_visits, stops_near

STOP = pl.DataFrame({"stop_id": ["100", "200"], "name": ["Union Sq", "Far away"],
                     "latitude": [40.7359, 40.80], "longitude": [-73.9899, -73.95]})
T0 = datetime(2026, 11, 3, 14, 0, tzinfo=UTC)  # 09:00 New York


def positions(vehicle, route, minutes_near, minutes_far):
    rows = []
    for m in minutes_near:
        rows.append((T0 + timedelta(minutes=m), vehicle, route, 40.7359, -73.9899))
    for m in minutes_far:
        rows.append((T0 + timedelta(minutes=m), vehicle, route, 40.7450, -73.9800))
    return rows


def frame(rows):
    return pl.DataFrame(rows, schema=["polled_at", "vehicle_key", "route_id", "latitude",
                                      "longitude"], orient="row")


def test_visits_split_on_gaps_and_headways_cross_vehicles():
    rows = (positions("bus1", "A", [0, 0.5, 1], [5, 10])
            + positions("bus1", "A", [20, 20.5], [])
            + positions("bus2", "A", [10, 10.5], []))
    visits = stop_visits(frame(rows), STOP)
    assert visits.height == 3
    assert visits["polls"].to_list() == [3, 2, 2]
    hw = headways(visits)
    assert hw["headway_min"].to_list()[1:] == pytest.approx([10, 10])
    summary = headway_summary(hw)
    assert summary["hour"].item() == 9
    assert summary["expected_wait_min"].item() == pytest.approx(5.0)


def test_stops_near_union_square():
    assert stops_near(STOP)["stop_id"].to_list() == ["100"]
