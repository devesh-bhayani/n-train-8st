"""Reconnaissance run: discover what the data sources actually look like.

Runs on GitHub Actions (which can reach data.ny.gov and friends) and writes small
JSON/CSV/HTML files describing each source, so download recipes can be written
against real column names instead of guesses.

    python -m n8st.data.recon --out _out/recon

Every item is independent: a failure is recorded in index.json and the run goes on.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import traceback
from collections.abc import Callable
from pathlib import Path

import requests

from n8st.config import DATASETS, SOCRATA_DOMAIN

UA = "n8st-research/0.1 (+https://github.com/devesh-bhayani/n-train-8st)"
TIMEOUT = 60

CATALOG_QUERIES = [
    "MTA subway origin-destination",
    "MTA subway hourly ridership",
    "MTA subway turnstile",
    "MTA subway customer journey",
    "MTA subway wait assessment",
    "MTA subway stations",
    "MTA subway trains delayed",
    "MTA daily ridership",
]

WIKI_SEARCHES = [
    "8th Street–New York University station",
    "Prince Street station BMT Broadway Line",
    "14th Street–Union Square station",
    "Canal Street station New York City Subway",
    "BMT Broadway Line",
    "34th Street–Herald Square station",
    "23rd Street station BMT Broadway Line",
    "28th Street station BMT Broadway Line",
    "N New York City Subway service",
    "W New York City Subway service",
    "Q New York City Subway service",
    "R New York City Subway service",
    "DeKalb Avenue station",
]

PAGES = {
    "mta_developers.html": "https://www.mta.info/developers",
    "api_mta_info.html": "https://api.mta.info/",
    "nyu_calendar.html": "https://www.nyu.edu/registrar/calendars/university-academic-calendar.html",
    "nyu_shuttle_routes.html": (
        "https://www.nyu.edu/life/travel-and-transportation/university-transportation/"
        "routes-and-schedules.html"
    ),
    "nyu_route_e.html": (
        "https://www.nyu.edu/life/travel-and-transportation/university-transportation/"
        "routes-and-schedules/route-e.html"
    ),
    "subwaydata_home.html": "https://subwaydata.nyc/",
}

GTFS_RT_FEEDS = {
    "nqrw": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
    "bdfm": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
}

SUBWAYDATA_META = "https://data.subwaydata.nyc/subwaydatanyc_metadata.json"

WEATHER_DAILY = (
    "https://archive-api.open-meteo.com/v1/archive?latitude=40.73&longitude=-73.99"
    "&start_date=2015-01-01&end_date={end}&timezone=America%2FNew_York"
    "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,snowfall_sum,"
    "precipitation_hours"
)
WEATHER_HOURLY = (
    "https://archive-api.open-meteo.com/v1/archive?latitude=40.73&longitude=-73.99"
    "&start_date=2022-01-01&end_date={end}&timezone=America%2FNew_York"
    "&hourly=temperature_2m,precipitation,snowfall"
)


def session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = UA
    return s


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, default=str))


def catalog(s: requests.Session, out: Path) -> dict:
    found = {}
    for q in CATALOG_QUERIES:
        r = s.get("https://api.us.socrata.com/api/catalog/v1",
                  params={"domains": SOCRATA_DOMAIN, "q": q, "limit": 40}, timeout=TIMEOUT)
        r.raise_for_status()
        for res in r.json().get("results", []):
            rsrc = res.get("resource", {})
            found[rsrc.get("id")] = {
                "name": rsrc.get("name"),
                "updated": rsrc.get("data_updated_at") or rsrc.get("updatedAt"),
                "columns": rsrc.get("columns_field_name"),
                "description": (rsrc.get("description") or "")[:400],
            }
    save_json(out / "catalog.json", found)
    return {"datasets_found": len(found)}


def dataset_meta(s: requests.Session, out: Path) -> dict:
    summary = {}
    for name, ds in DATASETS.items():
        try:
            meta = s.get(f"https://{SOCRATA_DOMAIN}/api/views/{ds}.json", timeout=TIMEOUT)
            meta.raise_for_status()
            m = meta.json()
            cols = [
                {"field": c.get("fieldName"), "type": c.get("dataTypeName"),
                 "name": c.get("name"), "description": (c.get("description") or "")[:300]}
                for c in m.get("columns", []) if not c.get("fieldName", ":").startswith(":")
            ]
            count = s.get(f"https://{SOCRATA_DOMAIN}/resource/{ds}.json",
                          params={"$select": "count(*) AS n"}, timeout=TIMEOUT).json()
            sample = s.get(f"https://{SOCRATA_DOMAIN}/resource/{ds}.json",
                           params={"$limit": 5}, timeout=TIMEOUT).json()
            info = {"id": ds, "title": m.get("name"), "rows": count,
                    "rows_updated_at": m.get("rowsUpdatedAt"), "columns": cols,
                    "sample": sample, "attachments": m.get("metadata", {}).get("attachments")}
            # Distinct values of low-cardinality time columns, to learn their encoding.
            distinct = {}
            for c in cols:
                f = c["field"]
                if re.search(r"(day_of_week|^month$|^year$|hour_of_day|fare_class|payment)", f):
                    d = s.get(f"https://{SOCRATA_DOMAIN}/resource/{ds}.json",
                              params={"$select": f"{f}, count(*) AS n", "$group": f,
                                      "$order": f, "$limit": 200}, timeout=TIMEOUT)
                    if d.ok:
                        distinct[f] = d.json()
            info["distinct"] = distinct
            save_json(out / "datasets" / f"{name}.json", info)
            summary[name] = {"ok": True, "rows": count, "columns": [c["field"] for c in cols]}
        except Exception as e:
            summary[name] = {"ok": False, "error": repr(e)[:300]}
    return summary


def wiki(s: requests.Session, out: Path) -> dict:
    got = {}
    for q in WIKI_SEARCHES:
        r = s.get("https://en.wikipedia.org/w/api.php",
                  params={"action": "query", "list": "search", "srsearch": q, "srlimit": 1,
                          "format": "json"}, timeout=TIMEOUT)
        hits = r.json().get("query", {}).get("search", [])
        if not hits:
            got[q] = None
            continue
        title = hits[0]["title"]
        p = s.get("https://en.wikipedia.org/w/api.php",
                  params={"action": "parse", "page": title, "prop": "wikitext",
                          "format": "json", "formatversion": 2}, timeout=TIMEOUT).json()
        text = p.get("parse", {}).get("wikitext", "")
        slug = re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")
        (out / "wiki").mkdir(parents=True, exist_ok=True)
        (out / "wiki" / f"{slug}.wikitext").write_text(text)
        got[q] = {"title": title, "chars": len(text)}
    save_json(out / "wiki" / "index.json", got)
    return {"pages": sum(1 for v in got.values() if v)}


def pages(s: requests.Session, out: Path) -> dict:
    res = {}
    for fname, url in PAGES.items():
        try:
            r = s.get(url, timeout=TIMEOUT)
            (out / "pages").mkdir(parents=True, exist_ok=True)
            (out / "pages" / fname).write_text(r.text)
            res[fname] = {"status": r.status_code, "chars": len(r.text)}
        except Exception as e:
            res[fname] = {"error": repr(e)[:200]}
    # NYU shuttle schedules are published as Google Sheets linked from the route pages.
    sheets = set()
    for fname in ("nyu_shuttle_routes.html", "nyu_route_e.html"):
        f = out / "pages" / fname
        if f.exists():
            sheets |= set(re.findall(r"docs\.google\.com/spreadsheets/d/([A-Za-z0-9_-]+)",
                                     f.read_text()))
    for sid in sorted(sheets)[:25]:
        try:
            r = s.get(f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv",
                      timeout=TIMEOUT)
            if r.ok and "," in r.text[:2000]:
                (out / "pages" / f"sheet_{sid}.csv").write_text(r.text)
                res[f"sheet_{sid}"] = {"status": r.status_code, "chars": len(r.text)}
        except Exception as e:
            res[f"sheet_{sid}"] = {"error": repr(e)[:200]}
    save_json(out / "pages" / "index.json", res)
    return {"pages": len(res)}


def gtfs_rt(s: requests.Session, out: Path) -> dict:
    from nyct_gtfs.compiled_gtfs import gtfs_realtime_pb2

    res = {}
    for name, url in GTFS_RT_FEEDS.items():
        r = s.get(url, timeout=TIMEOUT)
        info = {"status": r.status_code, "bytes": len(r.content)}
        if r.ok:
            msg = gtfs_realtime_pb2.FeedMessage()
            msg.ParseFromString(r.content)
            info["header_timestamp"] = msg.header.timestamp
            info["entities"] = len(msg.entity)
            info["trip_updates"] = sum(1 for e in msg.entity if e.HasField("trip_update"))
            info["vehicles"] = sum(1 for e in msg.entity if e.HasField("vehicle"))
            (out / "gtfs_rt").mkdir(parents=True, exist_ok=True)
            (out / "gtfs_rt" / f"{name}.pb").write_bytes(r.content)
        res[name] = info
    save_json(out / "gtfs_rt" / "index.json", res)
    return res


def subwaydata(s: requests.Session, out: Path) -> dict:
    r = s.get(SUBWAYDATA_META, timeout=TIMEOUT)
    r.raise_for_status()
    meta = r.json()
    save_json(out / "subwaydata" / "metadata.json", meta)
    days = meta.get("ProcessedDays", [])
    return {"days": len(days), "first": days[0]["Day"] if days else None,
            "last": days[-1]["Day"] if days else None,
            "example": days[-1] if days else None}


def weather(s: requests.Session, out: Path) -> dict:
    from datetime import date, timedelta

    end = (date.today() - timedelta(days=3)).isoformat()
    res = {}
    for name, tmpl, key in (("weather_daily.csv", WEATHER_DAILY, "daily"),
                            ("weather_hourly.csv", WEATHER_HOURLY, "hourly")):
        r = s.get(tmpl.format(end=end), timeout=TIMEOUT)
        r.raise_for_status()
        block = r.json()[key]
        cols = list(block)
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(cols)
        w.writerows(zip(*(block[c] for c in cols), strict=True))
        (out / "weather").mkdir(parents=True, exist_ok=True)
        (out / "weather" / name).write_text(buf.getvalue())
        res[name] = len(block[cols[0]])
    return res


ITEMS: dict[str, Callable[[requests.Session, Path], dict]] = {
    "catalog": catalog,
    "dataset_meta": dataset_meta,
    "wiki": wiki,
    "pages": pages,
    "gtfs_rt": gtfs_rt,
    "subwaydata": subwaydata,
    "weather": weather,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only", nargs="*", choices=sorted(ITEMS))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    s = session()
    index = {}
    for name, fn in ITEMS.items():
        if args.only and name not in args.only:
            continue
        try:
            index[name] = {"ok": True, "result": fn(s, args.out)}
        except Exception as e:
            index[name] = {"ok": False, "error": repr(e)[:500],
                           "trace": traceback.format_exc()[-1500:]}
        print(name, json.dumps(index[name], default=str)[:300])
    save_json(args.out / "index.json", index)


if __name__ == "__main__":
    main()
