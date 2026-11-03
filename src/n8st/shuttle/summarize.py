"""Data-quality summary of the shuttle log: coverage, gaps and buses seen per route.

    n8st-shuttle-summary [--dir data/raw/shuttle]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from n8st.shuttle.logger import DEFAULT_OUT


def summarize(shuttle_dir: Path) -> str:
    polls = f"{shuttle_dir}/polls/**/*.parquet"
    vehicles = f"{shuttle_dir}/vehicles/**/*.parquet"
    con = duckdb.connect()
    out = []
    out.append("Polls per service date (gaps = longest stretch between successful polls):")
    out.append(str(con.sql(f"""
        WITH ok AS (
            SELECT date, polled_at,
                   polled_at - lag(polled_at) OVER (PARTITION BY date ORDER BY polled_at) AS gap
            FROM read_parquet('{polls}', hive_partitioning = true) WHERE ok
        )
        SELECT p.date, count(*) AS polls, count(*) FILTER (WHERE p.ok) AS ok,
               round(100.0 * count(*) FILTER (WHERE p.ok) / count(*), 1) AS ok_pct,
               min(p.polled_at) AS first_poll, max(p.polled_at) AS last_poll,
               (SELECT max(gap) FROM ok WHERE ok.date = p.date) AS longest_gap
        FROM read_parquet('{polls}', hive_partitioning = true) p
        GROUP BY p.date ORDER BY p.date
    """)))
    try:
        out.append("\nDistinct vehicles and position rows per route and date:")
        out.append(str(con.sql(f"""
            SELECT date, route_name, route_id, count(DISTINCT vehicle_key) AS vehicles,
                   count(*) AS rows
            FROM read_parquet('{vehicles}', hive_partitioning = true)
            GROUP BY ALL ORDER BY date, route_name
        """)))
    except duckdb.IOException:
        out.append("\nNo vehicle rows yet (no buses running, or every poll failed).")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(summarize(args.dir))


if __name__ == "__main__":
    main()
