import pytest

from n8st.data import bulk


def test_ridership_editions_split_by_date():
    eds = bulk._ridership_editions("2019-06-01", "2025-03-01")
    assert [e[0] for e in eds] == ["hourly_ridership_2017_2019", "hourly_ridership_2020_2024",
                                   "hourly_ridership_2025"]
    assert eds[0][1:] == ("2019-06-01", "2020-01-01")
    assert eds[-1][1:] == ("2025-01-01", "2025-03-01")


def test_cli_parses_every_task(tmp_path, monkeypatch):
    seen = {}
    for name in bulk.TASKS:
        monkeypatch.setitem(bulk.TASKS, name, lambda out, args, n=name: seen.setdefault(n, args))
    bulk.main(["--out", str(tmp_path), "od-matrix", "2026", "9", "--daytype", "saturday"])
    bulk.main(["--out", str(tmp_path), "subwaydata", "2026-09-02", "2026-09-03"])
    bulk.main(["--out", str(tmp_path), "turnstile"])
    assert seen["od-matrix"].month == 9 and seen["od-matrix"].daytype == "saturday"
    assert seen["subwaydata"].start == "2026-09-02"
    assert "turnstile" in seen


def test_focus_stations_include_campus_and_home():
    for s in ("R21", "R20", "D20", "N05", "B17", "Q01"):
        assert s in bulk.FOCUS_GTFS


@pytest.mark.parametrize("daytype,n", [("weekday", 5), ("saturday", 1), ("sunday", 1)])
def test_daytypes(daytype, n):
    assert len(bulk.DAYTYPES[daytype]) == n
