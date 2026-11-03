.PHONY: setup test lint gtfs week1 stations ridership od data shuttle-once shuttle-log \
        shuttle-pull shuttle-summary wolk

setup:            ## install the environment (Python and packages, via uv)
	uv sync

test:             ## run the test suite
	uv run pytest -q

lint:
	uv run ruff check .

gtfs:             ## download the current MTA static GTFS
	uv run python -m n8st.data.gtfs download

week1: gtfs       ## schedule fact checks -> docs/findings/week1_gtfs_checks.md
	uv run python -m n8st.analysis.week1_checks

stations:         ## GTFS stop -> MTA complex ID lookup (run before ridership/od)
	uv run python -m n8st.data.datasets stations

ridership: stations
	uv run python -m n8st.data.datasets ridership --edition 2025

od: stations
	uv run python -m n8st.data.datasets od --year 2025

data: gtfs stations ridership od

shuttle-once:     ## one poll of the NYU shuttle feed, to check it works
	uv run n8st-shuttle-log --once

shuttle-log:      ## log shuttle positions until Ctrl-C (laptop or Raspberry Pi)
	uv run n8st-shuttle-log --duration-min 0

shuttle-pull:     ## copy the GitHub Action's shuttle data into data/raw/shuttle_remote
	git fetch origin shuttle-data:refs/remotes/origin/shuttle-data
	rm -rf data/raw/shuttle_remote && mkdir -p data/raw/shuttle_remote
	git archive refs/remotes/origin/shuttle-data shuttle | tar -x -C data/raw/shuttle_remote --strip-components=1

shuttle-summary:  ## coverage, gaps and buses per route
	uv run n8st-shuttle-summary --dir $(or $(DIR),data/raw/shuttle_remote)

wolk:             ## clone Josh Wolk's Stop the Stop pipeline (MIT) for Phase 0
	git clone https://github.com/WoshuaJolk/stopthestop-data external/stopthestop-data
