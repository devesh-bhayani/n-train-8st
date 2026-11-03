# Test fixtures

`passio_vehicles.json` and `passio_stops.json` are **synthetic**. Their shape follows
the parsing code in the unofficial PassioGo package (v0.2.2); the values are made up.
Once the logger has run against the live API, replace them with a real (trimmed)
response so the tests reflect what Passio actually sends.
