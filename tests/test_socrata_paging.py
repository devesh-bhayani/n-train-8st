import re

import duckdb

from n8st.data import socrata


class FakeResp:
    def __init__(self, text):
        self.content = text.encode()
        self.text = text


def fake_server(n_rows: int):
    """A dataset of n_rows rows (id, value) served like Socrata's CSV endpoint."""
    rows = [(f"row-{i:05d}", i) for i in range(n_rows)]
    calls = []

    def get(session, url, params=None):
        calls.append(dict(params))
        assert params["$order"] == ":id"
        assert "$offset" not in params  # keyset paging only
        after = None
        m = re.search(r":id > '([^']+)'", params.get("$where", ""))
        if m:
            after = m.group(1)
        sel = [r for r in rows if after is None or r[0] > after]
        if "value >= 10" in params.get("$where", ""):
            sel = [r for r in sel if r[1] >= 10]
        sel = sel[: params["$limit"]]
        body = '":id","value"\n' + "".join(f'"{a}","{b}"\n' for a, b in sel)
        return FakeResp(body)

    return get, calls


def test_keyset_paging_returns_every_row_once(tmp_path, monkeypatch):
    get, calls = fake_server(123)
    monkeypatch.setattr(socrata, "_get", get)
    out = socrata.download("abcd-1234", tmp_path / "x.parquet", select="value",
                           where="value >= 10", page_size=50)
    vals = [r[0] for r in duckdb.sql(f"SELECT value FROM '{out}' ORDER BY value").fetchall()]
    assert vals == list(range(10, 123))
    assert len(calls) == 3  # 50 + 50 + 13
    assert "(value >= 10) AND :id > 'row-00059'" == calls[1]["$where"]
    cols = [c[0] for c in duckdb.sql(f"DESCRIBE SELECT * FROM '{out}'").fetchall()]
    assert cols == ["value"]  # the :id helper column is dropped
