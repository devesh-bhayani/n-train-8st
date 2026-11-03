"""Minimal client for data.ny.gov (Socrata) with paging, retries and schema checks.

Set SOCRATA_APP_TOKEN (free from data.ny.gov -> Developer Settings) to avoid
throttling. Downloads land as CSV pages, then DuckDB merges them into one Parquet.
"""

from __future__ import annotations

import os
import shutil
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
    for attempt in range(5):
        resp = session.get(url, params=params, timeout=120)
        if resp.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** (attempt + 1))
            continue
        resp.raise_for_status()
        return resp
    resp.raise_for_status()
    return resp


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
) -> Path:
    """Page through a dataset (optionally filtered) and write a single Parquet file."""
    session = _session()
    pages_dir = out_parquet.with_suffix(".pages")
    if pages_dir.exists():
        shutil.rmtree(pages_dir)
    pages_dir.mkdir(parents=True)

    offset, page = 0, 0
    while True:
        params = {"$limit": page_size, "$offset": offset, "$order": ":id"}
        if where:
            params["$where"] = where
        if select:
            params["$select"] = select
        resp = _get(session, f"https://{domain}/resource/{dataset_id}.csv", params)
        body = resp.content
        n_rows = body.count(b"\n") - 1  # minus header; approximate if fields contain newlines
        if n_rows <= 0:
            break
        (pages_dir / f"part-{page:05d}.csv").write_bytes(body)
        print(f"  {dataset_id}: page {page} ({offset + n_rows:,} rows so far)")
        if n_rows < page_size:
            break
        offset += page_size
        page += 1

    out_parquet.parent.mkdir(parents=True, exist_ok=True)
    if not any(pages_dir.iterdir()):
        raise RuntimeError(f"{dataset_id}: no rows returned for where={where!r}")
    duckdb.sql(
        f"""
        COPY (
            SELECT * FROM read_csv('{pages_dir}/part-*.csv', header = true, union_by_name = true)
        ) TO '{out_parquet}' (FORMAT parquet)
        """
    )
    shutil.rmtree(pages_dir)
    return out_parquet
