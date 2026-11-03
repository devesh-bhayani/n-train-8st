import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import polars as pl

from n8st.shuttle import logger
from n8st.shuttle.passio import PassioError

FIX = Path(__file__).parent / "fixtures"


class FakeClient:
    def __init__(self, fail_on=()):
        self.calls = 0
        self.fail_on = set(fail_on)

    def vehicles_raw(self):
        self.calls += 1
        if self.calls in self.fail_on:
            raise PassioError("boom")
        return json.loads((FIX / "passio_vehicles.json").read_text())

    def routes_raw(self):
        return {"all": []}

    def stops_raw(self):
        return json.loads((FIX / "passio_stops.json").read_text())


class FakeTime:
    """Deterministic clock: each sleep advances both clocks."""

    def __init__(self, start):
        self.now = start
        self.mono = 0.0

    def clock(self):
        return self.now

    def monotonic(self):
        return self.mono

    def sleep(self, s):
        self.mono += s
        self.now += timedelta(seconds=s)


def run(tmp_path, client, start, **kw):
    t = FakeTime(start)
    return logger.run(client, out_dir=tmp_path, clock=t.clock, sleep=t.sleep,
                      monotonic=t.monotonic, **kw)


def test_run_writes_partitioned_parquet_and_poll_log(tmp_path):
    client = FakeClient(fail_on={2})
    stats = run(tmp_path, client, datetime(2026, 11, 3, 14, 0, tzinfo=UTC),
                interval_s=30, duration_s=150, flush_every=2)
    assert stats.polls == 5 and stats.ok == 4 and stats.vehicle_rows == 8

    vehicles = pl.read_parquet(tmp_path / "vehicles/**/*.parquet", hive_partitioning=True)
    assert vehicles.height == 8
    assert vehicles["date"].cast(pl.String).unique().to_list() == ["2026-11-03"]
    assert vehicles.schema["polled_at"] == pl.Datetime("us", "UTC")

    polls = pl.read_parquet(tmp_path / "polls/**/*.parquet")
    assert polls["ok"].to_list() == [True, False, True, True, True]
    assert polls.filter(~pl.col("ok"))["error"].item() == "boom"
    assert list((tmp_path / "meta").glob("date=2026-11-03/stops-*.json"))


def test_partition_uses_new_york_date(tmp_path):
    # 03:00 UTC on Nov 4 is 22:00 on Nov 3 in New York.
    run(tmp_path, FakeClient(), datetime(2026, 11, 4, 3, 0, tzinfo=UTC), once=True)
    assert (tmp_path / "vehicles" / "date=2026-11-03").is_dir()


def test_backoff_after_failures(tmp_path):
    client = FakeClient(fail_on={1, 2, 3})
    t = FakeTime(datetime(2026, 11, 3, 14, 0, tzinfo=UTC))
    waits = []

    def sleep(s):
        waits.append(s)
        t.sleep(s)

    logger.run(client, out_dir=tmp_path, interval_s=10, duration_s=200, clock=t.clock,
               sleep=sleep, monotonic=t.monotonic)
    assert waits[:4] == [10, 20, 40, 10]


def test_main_exit_code_reflects_success(tmp_path, monkeypatch):
    class Dead(FakeClient):
        def vehicles_raw(self):
            raise PassioError("down")

    monkeypatch.setattr(logger, "PassioClient", lambda system_id: Dead())
    assert logger.main(["--once", "--out", str(tmp_path)]) == 1
    monkeypatch.setattr(logger, "PassioClient", lambda system_id: FakeClient())
    assert logger.main(["--once", "--out", str(tmp_path)]) == 0
