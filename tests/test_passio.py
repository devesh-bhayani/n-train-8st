import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from n8st.shuttle.passio import parse_stops, parse_vehicles

FIX = Path(__file__).parent / "fixtures"
T = datetime(2026, 11, 3, 14, 15, tzinfo=UTC)


def test_parse_vehicles_skips_placeholder_and_types_fields():
    rows = parse_vehicles(json.loads((FIX / "passio_vehicles.json").read_text()), T)
    assert [r["vehicle_key"] for r in rows] == ["4521", "4522"]
    a, e = rows
    assert a["latitude"] == pytest.approx(40.7357)
    assert a["longitude"] == pytest.approx(-73.9905)
    assert a["route_name"] == "Route A"
    assert a["out_of_service"] is False
    assert json.loads(a["extra"]) == {"deviceId": 998877}
    assert e["speed"] is None and e["bus_type"] is None
    assert e["out_of_service"] is True
    assert e["extra"] is None


@pytest.mark.parametrize("raw", [[], {}, {"buses": []}, {"buses": {"-1": []}}])
def test_parse_vehicles_handles_empty_systems(raw):
    assert parse_vehicles(raw, T) == []


def test_parse_vehicles_requires_aware_timestamp():
    with pytest.raises(ValueError):
        parse_vehicles({}, datetime(2026, 11, 3))


def test_parse_stops():
    stops, route_stops = parse_stops(json.loads((FIX / "passio_stops.json").read_text()))
    assert {s["name"] for s in stops} == {"Union Square East", "Washington Square"}
    assert route_stops == [
        {"route_id": "61001", "position": 0, "stop_id": "100"},
        {"route_id": "61001", "position": 1, "stop_id": "200"},
    ]
