# Scenario ledger: does an N stop at 8 St–NYU save riders time?

OD: `od_synth.parquet` (888 weekday trips between 8:00 and 9:00). Departures sampled every 120 s; riders keep today's origin and destination stations (fixed OD), so benefits to riders who would *switch* to 8 St are not counted.

Costs are generalized: in-train minutes + 2 × waiting + 2 × walking + 5 min per transfer (base weights). Negative net = riders save time overall.

## Headline (base weights, passenger-hours per weekday)

| variant | trips_changed | added_s_per_trip | hours_saved | hours_lost | net_hours |
|---|---|---|---|---|---|
| V1 N local 34 St–Canal, MTA weekend timing | 241 | 150.0 | 2.0 | 8.0 | 7.0 |
| V2 N local 14 St–Canal only, observed timing | 241 | 110.0 | 1.0 | 11.0 | 10.0 |
| V1 N local 34 St–Canal, observed weekday timing | 241 | 210.0 | 1.0 | 15.0 | 14.0 |

## Robustness across the 13-cell weight grid

Wait/walk weight 1.5, 2, 2.5 × transfer penalty 0, 5, 10, 15 min, plus 2 × 30 min.

| variant | cells | cells_net_saving | best_net | worst_net |
|---|---|---|---|---|
| V1 N local 34 St–Canal, MTA weekend timing | 13 | 0 | 5.0 | 8.0 |
| V2 N local 14 St–Canal only, observed timing | 13 | 0 | 7.0 | 12.0 |
| V1 N local 34 St–Canal, observed weekday timing | 13 | 0 | 10.0 | 16.0 |

## V1 N local 34 St–Canal, observed weekday timing: net hours by weight

| wait & walk weight | transfer 0.0 min | transfer 5.0 min | transfer 10.0 min | transfer 15.0 min | transfer 30.0 min |
|---|---|---|---|---|---|
| 2.0 | 10.0 | 13.0 | 13.0 | 13.0 |  |
| 2.0 | 11.0 | 14.0 | 14.0 | 15.0 | 15.0 |
| 2.0 | 12.0 | 14.0 | 15.0 | 16.0 |  |

## Who gains under V1_obs (base weights)

Destinations with the most hours saved:

| destination | riders | hours_saved | avg_min_saved |
|---|---|---|---|
| Prince St (R W) | 2.0 | 0.3 | 9.2 |
| 8 St-NYU (R W) | 2.0 | 0.3 | 8.4 |
| 23 St (R W) | 2.0 | 0.2 | 4.9 |
| 28 St (R W) | 2.0 | 0.2 | 4.6 |
| Avenue M (Q) | 1.0 | 0.0 | 2.2 |
| Avenue J (Q) | 1.0 | 0.0 | 2.0 |
| Neck Rd (Q) | 1.0 | 0.0 | 1.9 |
| Ocean Pkwy (Q) | 1.0 | 0.0 | 1.9 |
| Brighton Beach (B Q) | 1.0 | 0.0 | 1.9 |
| Avenue U (Q) | 1.0 | 0.0 | 1.9 |

Origins with the most hours saved:

| origin | riders | hours_saved |
|---|---|---|
| 18 Av (N) | 32.0 | 1.2 |
| Astoria-Ditmars Blvd (N W) | 7.0 | 0.2 |

Biggest winning flows (origin → destination):

| origin | destination | riders | hours | min_per_rider |
|---|---|---|---|---|
| 18 Av (N) | Prince St (R W) | 1.0 | -0.3 | -15.1 |
| 18 Av (N) | 8 St-NYU (R W) | 1.0 | -0.2 | -13.7 |
| 18 Av (N) | 23 St (R W) | 1.0 | -0.1 | -6.8 |
| 18 Av (N) | 28 St (R W) | 1.0 | -0.1 | -6.1 |
| Astoria-Ditmars Blvd (N W) | Prince St (R W) | 1.0 | -0.1 | -3.3 |
| Astoria-Ditmars Blvd (N W) | 8 St-NYU (R W) | 1.0 | -0.1 | -3.2 |
| Astoria-Ditmars Blvd (N W) | 28 St (R W) | 1.0 | -0.1 | -3.1 |
| Astoria-Ditmars Blvd (N W) | 23 St (R W) | 1.0 | -0.1 | -3.0 |
| 18 Av (N) | Avenue M (Q) | 1.0 | -0.0 | -2.2 |
| 18 Av (N) | Avenue J (Q) | 1.0 | -0.0 | -2.0 |
| 18 Av (N) | Ocean Pkwy (Q) | 1.0 | -0.0 | -1.9 |
| 18 Av (N) | Neck Rd (Q) | 1.0 | -0.0 | -1.9 |

## Who loses under V1_obs

Origins with the most hours lost:

| origin | riders | hours_lost |
|---|---|---|
| 18 Av (N) | 241.0 | 12.4 |
| Astoria-Ditmars Blvd (N W) | 113.0 | 2.5 |

Biggest losing flows:

| origin | destination | riders | hours | min_per_rider |
|---|---|---|---|---|
| 18 Av (N) | Roosevelt Island (M) | 1.0 | 0.1 | 7.4 |
| 18 Av (N) | 21 St-Queensbridge (M) | 1.0 | 0.1 | 7.4 |
| 18 Av (N) | Eastchester-Dyre Av (5) | 1.0 | 0.1 | 7.1 |
| 18 Av (N) | Pelham Pkwy (5) | 1.0 | 0.1 | 7.1 |
| 18 Av (N) | Morris Park (5) | 1.0 | 0.1 | 7.1 |
| 18 Av (N) | Gun Hill Rd (5) | 1.0 | 0.1 | 7.1 |
| 18 Av (N) | Baychester Av (5) | 1.0 | 0.1 | 7.1 |
| 18 Av (N) | Avenue X (F) | 1.0 | 0.1 | 6.7 |
| 18 Av (N) | Avenue U (F) | 1.0 | 0.1 | 6.7 |
| 18 Av (N) | Neptune Av (F) | 1.0 | 0.1 | 6.7 |
| 18 Av (N) | Kings Hwy (F) | 1.0 | 0.1 | 6.6 |
| 18 Av (N) | Avenue P (F) | 1.0 | 0.1 | 6.3 |

## Net hours by hour of the day (base weights)

| hour | V1_sched | V1_obs | V2_obs |
|---|---|---|---|
| 8 | 6.6 | 13.6 | 10.0 |
