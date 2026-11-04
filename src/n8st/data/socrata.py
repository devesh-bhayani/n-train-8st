"""Minimal client for data.ny.gov (Socrata) with paging, retries and schema checks.

Set SOCRATA_APP_TOKEN (free from data.ny.gov -> Developer Settings) to avoid
throttling. Downloads land as CSV pages, then DuckDB merges them into one Parquet.
"""

from __future__ import annotations

import csv
import os
import shutil
import tempfile
import time
from collections.abc import Iterable
from pathlib import Path

import duckdb
import requests

from n8st.config import SOCRATA_DOMAIN, USER_AGENT

PAGE_SIZE = 50_000


class SchemaError(RuntimeError):
    pass


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    token = os.environ.get("SOCRATA_APP_TOKEN")
    if token:
        s.headers["X-App-Token"] = token
    return s


def _get(session: requests.Session, url: str, params: dict | None = None) -> requests.Response:
    """GET with retries on throttling, server errors and timeouts (aggregations can be slow)."""
    last_error: Exception | None = None
    for attempt in range(6):
        try:
            resp = session.get(url, params=params, timeout=600)
            _ = resp.content  # read the whole body inside the retry (resets happen mid-stream)
        except (requests.Timeout, requests.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ContentDecodingError) as e:
            last_error = e
            time.sleep(min(2 ** (attempt + 2), 120))
            continue
        if resp.status_code in (429, 500, 502, 503, 504):
            last_error = requests.HTTPError(f"{resp.status_code}: {resp.text[:300]}")
            time.sleep(min(2 ** (attempt + 2), 120))
            continue
        if not resp.ok:
            raise requests.HTTPError(f"{resp.status_code} for {resp.url}: {resp.text[:500]}")
        return resp
    raise RuntimeError(f"gave up after retries: {last_error}")


def columns(dataset_id: str, domain: str = SOCRATA_DOMAIN) -> list[str]:
    """API field names of a dataset, from its metadata."""
    meta = _get(_session(), f"https://{domain}/api/views/{dataset_id}.json").json()
    return [c["fieldName"] for c in meta["columns"] if not c["fieldName"].startswith(":")]


def require_columns(dataset_id: str, needed: Iterable[str]) -> list[str]:
    """Fail loudly if a dataset no longer has the columns a recipe depends on."""
    have = columns(dataset_id)
    missing = [c for c in needed if c not in have]
    if missing:
        raise SchemaError(
            f"{dataset_id} is missing columns {missing}. Available columns: {have}"
        )
    return have


def sql_in(column: str, values: Iterable[str | int]) -> str:
    """Build a SoQL `column IN (...)` clause, quoting values as strings."""
    quoted = ", ".join("'" + str(v).replace("'", "''") + "'" for v in values)
    return f"{column} IN ({quoted})"


def download(
    dataset_id: str,
    out_parquet: Path,
    where: str | None = None,
    select: str | None = None,
    page_size: int = PAGE_SIZE,
    domain: str = SOCRATA_DOMAIN,
    group: str | None = None,
    having: str | None = None,
    order: str | None = None,
) -> Path:
    """Page through a dataset (optionally filtered or aggregated) into one Parquet file.

    Plain (non-aggregated) queries use keyset paging on Socrata's row id: each page asks
    for rows with `:id` greater than the last one seen, so every page costs the same.
    ($offset paging re-scans all earlier rows on every page, which is quadratic.)
    Aggregated queries (`group`) page with $offset, ordered by `order` or the group keys.
    """
    session = _session()
    pages_dir = Path(tempfile.mkdtemp(prefix="socrata_"))  # never inside the output folder
    # Keyset paging needs an explicit column list (SoQL rejects ":id, *"); small full-table
    # pulls without `select` fall back to $offset, which is fine at that size.
    keyset = group is None and select is not None
    sel = (":id, " + select) if keyset else select

    offset, page, total, last_id = 0, 0, 0, None
    while True:
        params: dict = {"$limit": page_size}
        if keyset:
            params["$order"] = ":id"
            clause = where or ""
            if last_id is not None:
                clause = f"({clause}) AND :id > '{last_id}'" if clause else f":id > '{last_id}'"
            if clause:
                params["$where"] = clause
        else:
            params["$offset"] = offset
            params["$order"] = order or group or ":id"
            if where:
                params["$where"] = where
        for key, value in (("$select", sel), ("$group", group), ("$having", having)):
            if value:
                params[key] = value
        t = time.monotonic()
        resp = _get(session, f"https://{domain}/resource/{dataset_id}.csv", params)
        body = resp.content
        lines = body.splitlines()
        n_rows = len(lines) - 1  # minus header
        if n_rows <= 0:
            break
        (pages_dir / f"part-{page:05d}.csv").write_bytes(body)
        total += n_rows
        print(f"  {dataset_id}: page {page} ({total:,} rows so far, "
              f"{time.monotonic() - t:.1f}s)", flush=True)
        if n_rows < page_size:
            break
        if keyset:
            header = next(csv.reader([lines[0].decode()]))
            last = next(csv.reader([lines[-1].decode()]))
            last_id = last[header.index(":id")]
        offset += page_size
        page += 1

    out_parquet.parent.mkdir(parents=True, exist_ok=True)
    if not any(pages_dir.iterdir()):
        raise RuntimeError(f"{dataset_id}: no rows returned for where={where!r}")
    exclude = ' EXCLUDE (":id")' if keyset else ""
    duckdb.sql(
        f"""
        COPY (
            SELECT *{exclude}
            FROM read_csv('{pages_dir}/part-*.csv', header = true, union_by_name = true)
        ) TO '{out_parquet}' (FORMAT parquet)
        """
    )
    shutil.rmtree(pages_dir)
    return out_parquet
