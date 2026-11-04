# Observed service on the Broadway line

subwaydata.nyc observed trips, 2026-09-02 to 2026-11-03: holiday 1 days, saturday 9 days, sunday 9 days, weekday 44 days.
Times are the last real-time prediction before each train passed a stop (accurate to ~30 s).

## 1. Your backtrack: downtown R/W at 14 St–Union Sq (weekdays)

Gaps between consecutive downtown R or W trains, and the average wait for a rider who arrives at a random moment. Gaps over 30 min (service breaks) are excluded.

| hour | trains_per_hour | median_gap | p90_gap | expected_wait |
|---|---|---|---|---|
| 6 | 6.6 | 9.2 | 14.2 | 5.6 |
| 7 | 13.3 | 3.8 | 8.6 | 3.3 |
| 8 | 15.3 | 3.4 | 6.8 | 2.6 |
| 9 | 14.6 | 3.7 | 7.1 | 2.7 |
| 10 | 13.1 | 4.0 | 8.2 | 3.0 |
| 11 | 12.7 | 4.2 | 8.4 | 3.1 |
| 12 | 12.6 | 4.2 | 8.4 | 3.2 |
| 13 | 13.3 | 4.0 | 7.7 | 3.0 |
| 14 | 12.3 | 4.1 | 8.5 | 3.3 |
| 15 | 13.1 | 3.9 | 8.4 | 3.0 |
| 16 | 13.2 | 3.8 | 8.1 | 3.0 |
| 17 | 15.0 | 3.2 | 7.6 | 2.8 |
| 18 | 12.7 | 4.1 | 8.2 | 3.1 |
| 19 | 12.4 | 4.3 | 8.6 | 3.3 |
| 20 | 10.8 | 4.6 | 9.8 | 3.6 |
| 21 | 10.2 | 5.0 | 10.6 | 3.9 |
| 22 | 5.4 | 10.0 | 15.8 | 6.0 |
| 23 | 1.5 | 13.1 | 17.0 | 7.2 |

## 2. Downtown N, 34 St–Herald Sq to Canal St (bridge level), 7 am–9 pm

`local = true` runs stopped at 8 St–NYU (the weekend pattern). The difference in medians is the observed cost of running the N local, per through-rider.

| daytype | local | trips | median_s | p25_s | p75_s | p90_s |
|---|---|---|---|---|---|---|
| holiday | True | 75 | 670.0 | 635.0 | 700.0 | 740.0 |
| saturday | False | 7 | 565.0 | 550.0 | 675.0 | 675.0 |
| saturday | True | 632 | 682.0 | 645.0 | 728.0 | 770.0 |
| sunday | False | 7 | 469.0 | 455.0 | 605.0 | 605.0 |
| sunday | True | 596 | 680.0 | 640.0 | 721.0 | 793.0 |
| weekday | False | 4138 | 419.0 | 400.0 | 440.0 | 470.0 |
| weekday | True | 101 | 435.0 | 417.0 | 614.0 | 815.0 |

Observed local-minus-express: **+262 s** (Saturday local vs weekday express medians).

## 3. Your commute legs, observed in-train minutes (weekdays, 7–10 am departures)

| leg | trips | median_min | p90_min |
|---|---|---|---|
| D 71 St → W 4 St | 960 | 35.3 | 40.7 |
| N 18 Av → 14 St | 990 | 34.9 | 39.1 |
| N 18 Av → Canal | 987 | 30.3 | 33.9 |
| R/W 14 St → 8 St (backtrack ride) | 1069 | 1.8 | 2.3 |
| R Canal → 8 St | 1002 | 3.2 | 3.5 |

## 4. Waiting at home, weekdays 7–10 am

| platform | trains_per_hour | median_gap | expected_wait |
|---|---|---|---|
| D at 71 St (toward Manhattan) | 7.3 | 7.8 | 4.8 |
| N at 18 Av (toward Manhattan) | 7.8 | 7.3 | 4.6 |
