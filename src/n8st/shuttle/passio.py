"""Thin client for the public Passio GO endpoints behind passiogo.com.

Endpoints and request bodies follow the unofficial `PassioGo` package
(github.com/athuler/PassioGo, v0.2.2). We don't depend on that package because
its Vehicle class drops latitude, and because we want to keep every field the
API returns (unknown fields go into an `extra` JSON column).

The API is undocumented and can change without notice. Poll gently.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import requests

from n8st.config import NYU_PASSIO_SYSTEM_ID, PASSIO_BASE_URL, USER_AGENT

# Vehicle fields we map to typed columns: API name -> our column name.
VEHICLE_FIELDS = {
    "busId": "bus_id",
    "busName": "bus_name",
    "busType": "bus_type",
    "routeId": "route_id",
    "route": "route_name",
    "tripId": "trip_id",
    "latitude": "latitude",
    "longitude": "longitude",
    "speed": "speed",
    "calculatedCourse": "course",
    "paxLoad100": "pax_load",
    "outOfService": "out_of_service",
    "created": "passio_created",
    "color": "color",
}
FLOAT_COLS = {"latitude", "longitude", "speed", "course", "pax_load"}


class PassioError(RuntimeError):
    pass


class PassioClient:
    def __init__(
        self,
        system_id: int = NYU_PASSIO_SYSTEM_ID,
        base_url: str = PASSIO_BASE_URL,
        timeout: float = 20,
    ):
        self.system_id = system_id
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT

    def _post(self, query: str, body: dict[str, Any]) -> dict[str, Any] | list:
        resp = self.session.post(f"{self.base_url}/mapGetData.php?{query}", json=body,
                                 timeout=self.timeout)
        resp.raise_for_status()
        try:
            data = resp.json()
        except ValueError as e:
            raise PassioError(f"non-JSON response: {resp.text[:200]!r}") from e
        if isinstance(data, dict) and data.get("error"):
            raise PassioError(f"API error: {data['error']}")
        return data

    def vehicles_raw(self) -> dict[str, Any] | list:
        return self._post("getBuses=2", {"s0": str(self.system_id), "sA": 1})

    def routes_raw(self) -> dict[str, Any] | list:
        return self._post("getRoutes=1", {"systemSelected0": str(self.system_id), "amount": 1})

    def stops_raw(self) -> dict[str, Any] | list:
        return self._post("getStops=2", {"s0": str(self.system_id), "sA": 1})


def _to_float(v: Any) -> float | None:
    try:
        return None if v in (None, "") else float(v)
    except (TypeError, ValueError):
        return None


def parse_vehicles(raw: dict[str, Any] | list, polled_at: datetime) -> list[dict[str, Any]]:
    """Flatten a getBuses response into one row per vehicle.

    Response shape: {"buses": {"<vehicle key>": [{...fields...}], "-1": ...}}.
    "-1" is a placeholder entry; an empty system can come back as a list.
    """
    if polled_at.tzinfo is None:
        raise ValueError("polled_at must be timezone-aware")
    buses = raw.get("buses", {}) if isinstance(raw, dict) else {}
    if not isinstance(buses, dict):
        return []
    rows = []
    for key, value in buses.items():
        if key == "-1":
            continue
        record = value[0] if isinstance(value, list) and value else value
        if not isinstance(record, dict):
            continue
        row: dict[str, Any] = {
            "polled_at": polled_at.astimezone(UTC),
            "vehicle_key": str(key),
        }
        for api_name, col in VEHICLE_FIELDS.items():
            v = record.get(api_name)
            if col in FLOAT_COLS:
                row[col] = _to_float(v)
            elif col == "out_of_service":
                row[col] = None if v is None else str(v) in ("1", "true", "True")
            else:
                row[col] = None if v is None else str(v)
        extra = {k: v for k, v in record.items() if k not in VEHICLE_FIELDS}
        row["extra"] = json.dumps(extra, sort_keys=True, default=str) if extra else None
        rows.append(row)
    return rows


def parse_stops(raw: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (stops, route_stops) from a getStops response.

    stops:       one row per stop with name and coordinates.
    route_stops: one row per (route, position, stop) - the stop order on each route.
    """
    stops_obj = raw.get("stops") or {}
    routes_obj = raw.get("routes") or {}
    stops = []
    for stop in (stops_obj.values() if isinstance(stops_obj, dict) else []):
        stops.append(
            {
                "stop_id": str(stop.get("id")),
                "name": stop.get("name"),
                "latitude": _to_float(stop.get("latitude")),
                "longitude": _to_float(stop.get("longitude")),
                "radius_m": _to_float(stop.get("radius")),
            }
        )
    route_stops = []
    for route_id, entries in (routes_obj.items() if isinstance(routes_obj, dict) else []):
        # entries = [route name, colour, [position, stop_id, ...], [position, stop_id, ...], ...]
        position = 0
        for entry in entries[2:]:
            if not isinstance(entry, list) or len(entry) < 2:
                continue
            route_stops.append(
                {"route_id": str(route_id), "position": position, "stop_id": str(entry[1])}
            )
            position += 1
    return stops, route_stops


def now_utc() -> datetime:
    return datetime.now(UTC)
