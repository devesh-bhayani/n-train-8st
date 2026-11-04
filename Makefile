.PHONY: setup test lint gtfs week1 stations ridership od data shuttle-once shuttle-log \
        shuttle-pull shuttle-summary shuttle-first-look wolk phase0 mta-pull observed ledger \
        sim calibrate commute experiment2016 dashboard-data app

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

shuttle-first-look:  ## stops, routes and headways near Union Square -> docs/findings/
	uv run python -m n8st.analysis.shuttle_first_look --dir $(or $(DIR),data/raw/shuttle_remote)

wolk:             ## clone Josh Wolk's Stop the Stop pipeline (MIT) for Phase 0
	git clone https://github.com/WoshuaJolk/stopthestop-data external/stopthestop-data

phase0:           ## independent replication of Stop the Stop + 8 St-NYU sensitivity
	uv run python -m n8st.analysis.wolk_replication

mta-pull:         ## copy the fetch-data workflow's downloads into data/raw/mta_data
	git fetch origin mta-data:refs/remotes/origin/mta-data
	rm -rf data/raw/mta_data && mkdir -p data/raw/mta_data
	git archive refs/remotes/origin/mta-data | tar -x -C data/raw/mta_data

observed:         ## observed headways, waits and running times -> docs/findings/observed_service.md
	uv run python -m n8st.analysis.observed

OD ?= data/raw/mta_data/bulk/od/od_weekday_2026_09.parquet
ledger:           ## scenario ledger for one OD month -> docs/findings/ledger_*.md
	uv run python -m n8st.ledger.run --od $(OD)
	uv run python -m n8st.ledger.report data/processed/ledger_$(subst od_,,$(basename $(notdir $(OD))))

calibrate:        ## fit the simulation's free parameters to observed trains
	uv run python -m n8st.sim.calibrate --days 8

sim:              ## run the Broadway simulation (base, V1, V2) -> docs/findings/simulation.md
	uv run python -m n8st.sim.experiment --seeds 3

commute:          ## replay the 18 Av commute on real trains + recommender -> docs/findings/commute.md
	uv run python -m n8st.analysis.commute

experiment2016:   ## natural experiment on Nov 7, 2016 -> docs/findings/natural_experiment_2016.md
	uv run python -m n8st.analysis.natural_experiment

dashboard-data:   ## export the small tables the dashboard reads (app/data/)
	uv run python -m n8st.dashboard_data

app:              ## run the Streamlit dashboard locally
	uv run --extra app streamlit run app/streamlit_app.py
