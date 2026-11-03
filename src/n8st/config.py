"""Project-wide constants: paths, station IDs, dataset IDs.

Anything marked VERIFY has not yet been checked against the source. Check it
and update the comment (with the date) before relying on it in an analysis.
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("N8ST_DATA_DIR", PROJECT_ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
FINDINGS_DIR = PROJECT_ROOT / "docs" / "findings"

NYC_TZ = "America/New_York"

# --- GTFS parent-station IDs ------------------------------------------------
# Verified against MTA static GTFS (feed valid 2026-11-01 to 2027-05-15).
STOPS = {
    "R17": "34 St-Herald Sq (Broadway line)",
    "R18": "28 St",
    "R19": "23 St",
    "R20": "14 St-Union Sq (Broadway line)",
    "R21": "8 St-NYU",
    "R22": "Prince St",
    "R23": "Canal St (Broadway local level)",
    "Q01": "Canal St (Manhattan Bridge level)",
    "D20": "W 4 St-Wash Sq",
    "636": "Astor Pl",
    "N05": "18 Av (Sea Beach line, N)",
    "B17": "71 St (West End line, D)",
}

EIGHT_ST = "R21"
UNION_SQ_BWAY = "R20"
HERALD_SQ_BWAY = "R17"
CANAL_BRIDGE = "Q01"
CANAL_LOCAL = "R23"

# Sea Beach line (N in Brooklyn), north to south. Verified in the same feed.
SEA_BEACH_STOPS = ["N02", "N03", "N04", "N05", "N06", "N07", "N08", "N09", "N10"]

# Stations around campus, used to filter origin-destination pulls.
CAMPUS_AREA_STOPS = ["R21", "R22", "R20", "D20", "636", "R23", "Q01"]
# The user's home corridor (both lines they can walk to).
HOME_STOPS = ["N05", "B17"]

# --- Static GTFS ------------------------------------------------------------
GTFS_URLS = {
    # Regular schedule (reachable 2026-11-03).
    "subway": "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip",
    # Includes planned work for roughly the next 7 days. VERIFY URL.
    "supplemented": "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_supplemented.zip",
}

# --- data.ny.gov (Socrata) dataset IDs -------------------------------------
# From the research notes (docs/research). Column names are checked at run
# time against each dataset's metadata, so a renamed column fails loudly.
SOCRATA_DOMAIN = "data.ny.gov"
DATASETS = {
    "stations": "39hk-dx4f",  # MTA Subway Stations (GTFS stop -> complex ID)
    "complexes": "5f5g-n3cz",  # MTA Subway Stations and Complexes
    "entrances": "i9wp-a4ja",  # MTA Subway Entrances and Exits: 2024
    "hourly_ridership_2025": "5wq4-mkjj",  # Beginning 2025
    "hourly_ridership_2020_2024": "wujg-7c2s",  # actually starts Feb 2022
    "od_2023": "uhf3-t34z",
    "od_2024": "jsu2-fbtj",
    "od_2025": "y2qv-fytt",
    "od_2026": "28vm-gjqr",  # Jan-Aug 2026, used by Stop the Stop. VERIFY edition.
    "turnstile_2016": "ekwu-khcy",  # legacy MetroCard turnstile counts
    "cjm_2015_2019": "r7qk-6tcy",  # Customer Journey Metrics
    "cjm_2020_2024": "4apg-4kt9",
    "cjm_2025": "s4u6-t435",
    "wait_assessment_2025": "62c4-mvcx",
}

# --- NYU shuttle (Passio GO) -----------------------------------------------
PASSIO_BASE_URL = "https://passiogo.com"
NYU_PASSIO_SYSTEM_ID = 1007  # from passiogo.com/?agency=1007. VERIFY on first run.

USER_AGENT = "n8st-research/0.1 (student transit research project)"
