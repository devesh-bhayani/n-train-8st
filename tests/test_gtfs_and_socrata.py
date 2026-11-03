import polars as pl

from n8st.analysis.week1_checks import headways
from n8st.data.gtfs import time_to_seconds
from n8st.data.socrata import sql_in


def test_time_to_seconds_handles_after_midnight():
    df = pl.DataFrame({"t": ["00:00:30", "08:15:00", "25:13:30"]})
    assert df.select(time_to_seconds(pl.col("t")))["t"].to_list() == [30, 29700, 90810]


def test_scheduled_headways_and_expected_wait():
    # Trains at 08:00, 08:02, 08:10: headways 2 and 8 min -> wait = (4+64)/(2*10) = 3.4 min
    ev = pl.DataFrame({
        "parent_stop": ["R21"] * 3, "route_id": ["R", "W", "R"],
        "service_id": ["Weekday"] * 3, "direction": ["S"] * 3,
        "dep_s": [28800, 28920, 29400],
    })
    out = headways(ev, "R21", ["R", "W"], "Weekday")
    assert out["trains"].item() == 3
    assert out["expected_wait_min"].item() == 3.4


def test_sql_in_quotes_values():
    assert sql_in("complex_id", [16, "O'Hare"]) == "complex_id IN ('16', 'O''Hare')"
