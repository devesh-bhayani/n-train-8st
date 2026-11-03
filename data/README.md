# data/

Nothing here is committed except this file. Rebuild with `make data` and `make gtfs`.

```
raw/gtfs/        MTA static GTFS zips, named by feed start date
raw/mta/         data.ny.gov pulls (stations, hourly ridership, origin-destination)
raw/shuttle/     shuttle logger output when run locally
raw/shuttle_remote/  shuttle data pulled from the shuttle-data branch (make shuttle-pull)
interim/         cleaned, joined tables
processed/       model inputs and results
```
