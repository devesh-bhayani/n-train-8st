# Week-1 GTFS checks

Generated 2026-11-03 from MTA static GTFS valid 20261101 to 20270515. These are *scheduled* times; observed trains will differ.

## 1. Routes stopping at 8 St-NYU (trips per day, both directions)

| route_id | band | Weekday | Saturday | Sunday |
|---|---|---|---|---|
| N | day 06-21 | 0 | 149 | 149 |
| N | evening 21-24 | 7 | 31 | 31 |
| N | late night 00-06 | 37 | 36 | 36 |
| Q | evening 21-24 | 4 | 5 | 3 |
| Q | late night 00-06 | 38 | 38 | 37 |
| R | day 06-21 | 232 | 149 | 149 |
| R | evening 21-24 | 28 | 26 | 26 |
| R | late night 00-06 | 1 | 1 | 1 |
| W | day 06-21 | 173 | 0 | 0 |
| W | evening 21-24 | 14 | 0 | 0 |

## 2. W trips on the Sea Beach line

Direction N = toward Manhattan. Times are departures from 18 Av.

| service_id | direction | via_montague | trips | stop_18_av | stop_8_st | earliest_18_av | latest_18_av |
|---|---|---|---|---|---|---|---|
| Weekday | S | True | 1 | 1 | 1 | 21:54 | 21:54 |
| Weekday | N | True | 2 | 2 | 2 | 07:12 | 16:41 |

Each trip:

| trip_id | service_id | direction | at_18_av | at_8_st | via_montague | first_stop | last_stop |
|---|---|---|---|---|---|---|---|
| BFA26GEN-N103-Weekday-00_042450_N..N70R | Weekday | N | 07:12 | 07:58 | True | N10 | R01 |
| BFA26GEN-N103-Weekday-00_099300_N..N70R | Weekday | N | 16:41 | 17:27 | True | N10 | R01 |
| BFA26GEN-N103-Weekday-00_123650_N..S70R | Weekday | S | 21:54 | 21:06 | True | R01 | N10 |

## 3. Scheduled R/W departures, weekdays

Direction S = downtown. Your 14 St backtrack is a downtown R/W from 14 St (R20).

### At 14 St-Union Sq (R20)

| direction | hour | trains | median_headway_min | max_headway_min | expected_wait_min |
|---|---|---|---|---|---|
| N | 6 | 5 | 12.0 | 15.5 | 6.4 |
| N | 7 | 13 | 5.5 | 10.0 | 3.4 |
| N | 8 | 15 | 4.5 | 6.0 | 2.3 |
| N | 9 | 14 | 3.8 | 7.0 | 2.5 |
| N | 10 | 14 | 4.0 | 7.5 | 2.5 |
| N | 11 | 13 | 4.0 | 6.5 | 2.6 |
| N | 12 | 14 | 5.2 | 7.5 | 2.7 |
| N | 13 | 13 | 4.5 | 8.0 | 2.7 |
| N | 14 | 14 | 4.5 | 7.5 | 2.6 |
| N | 15 | 14 | 4.0 | 6.0 | 2.3 |
| N | 16 | 15 | 4.5 | 7.0 | 2.4 |
| N | 17 | 15 | 4.0 | 6.5 | 2.3 |
| N | 18 | 15 | 4.5 | 6.5 | 2.4 |
| N | 19 | 14 | 4.2 | 7.0 | 2.6 |
| N | 20 | 13 | 4.5 | 7.0 | 2.5 |
| N | 21 | 11 | 5.5 | 10.5 | 3.4 |
| N | 22 | 8 | 5.5 | 14.0 | 4.1 |
| N | 23 | 4 | 13.2 | 14.5 | 6.7 |
| S | 5 | 1 |  |  | nan |
| S | 6 | 7 | 9.0 | 14.0 | 5.1 |
| S | 7 | 14 | 3.8 | 7.5 | 2.6 |
| S | 8 | 17 | 3.5 | 8.0 | 2.2 |
| S | 9 | 14 | 3.5 | 6.5 | 2.3 |
| S | 10 | 14 | 4.8 | 8.5 | 2.7 |
| S | 11 | 14 | 4.0 | 7.5 | 2.7 |
| S | 12 | 13 | 4.5 | 7.5 | 2.5 |
| S | 13 | 14 | 5.2 | 7.5 | 2.7 |
| S | 14 | 13 | 5.0 | 7.0 | 2.6 |
| S | 15 | 14 | 4.5 | 7.0 | 2.5 |
| S | 16 | 14 | 4.2 | 8.0 | 2.8 |
| S | 17 | 16 | 3.8 | 6.5 | 2.3 |
| S | 18 | 13 | 4.0 | 7.5 | 2.6 |
| S | 19 | 14 | 4.5 | 10.0 | 3.0 |
| S | 20 | 13 | 5.5 | 8.0 | 3.0 |
| S | 21 | 12 | 4.8 | 6.5 | 2.6 |
| S | 22 | 5 | 10.0 | 11.0 | 5.1 |
| S | 23 | 2 | 12.2 | 12.5 | 6.1 |

### At 8 St-NYU (R21)

| direction | hour | trains | median_headway_min | max_headway_min | expected_wait_min |
|---|---|---|---|---|---|
| N | 6 | 5 | 12.0 | 15.5 | 6.4 |
| N | 7 | 13 | 5.5 | 10.0 | 3.4 |
| N | 8 | 15 | 4.5 | 6.0 | 2.3 |
| N | 9 | 15 | 5.0 | 7.0 | 2.5 |
| N | 10 | 13 | 4.0 | 7.5 | 2.5 |
| N | 11 | 14 | 4.5 | 6.5 | 2.6 |
| N | 12 | 13 | 5.0 | 7.5 | 2.6 |
| N | 13 | 14 | 4.8 | 8.0 | 2.8 |
| N | 14 | 13 | 4.5 | 7.5 | 2.5 |
| N | 15 | 15 | 4.0 | 7.0 | 2.4 |
| N | 16 | 14 | 4.2 | 6.5 | 2.2 |
| N | 17 | 15 | 4.0 | 6.5 | 2.3 |
| N | 18 | 15 | 4.5 | 6.5 | 2.4 |
| N | 19 | 14 | 4.2 | 7.0 | 2.6 |
| N | 20 | 14 | 4.5 | 7.0 | 2.4 |
| N | 21 | 11 | 5.5 | 10.5 | 3.3 |
| N | 22 | 7 | 5.5 | 14.0 | 4.3 |
| N | 23 | 4 | 13.2 | 14.5 | 6.7 |
| S | 5 | 1 |  |  | nan |
| S | 6 | 7 | 9.0 | 14.0 | 5.1 |
| S | 7 | 14 | 3.8 | 7.5 | 2.6 |
| S | 8 | 16 | 3.5 | 8.0 | 2.2 |
| S | 9 | 15 | 3.0 | 6.5 | 2.2 |
| S | 10 | 14 | 4.8 | 8.5 | 2.7 |
| S | 11 | 13 | 3.5 | 7.5 | 2.6 |
| S | 12 | 14 | 5.0 | 7.5 | 2.6 |
| S | 13 | 13 | 5.0 | 7.5 | 2.7 |
| S | 14 | 14 | 5.2 | 7.0 | 2.6 |
| S | 15 | 14 | 4.5 | 7.0 | 2.5 |
| S | 16 | 13 | 4.0 | 8.0 | 2.7 |
| S | 17 | 16 | 3.8 | 7.0 | 2.4 |
| S | 18 | 14 | 4.2 | 7.5 | 2.6 |
| S | 19 | 13 | 4.5 | 10.0 | 2.9 |
| S | 20 | 13 | 6.5 | 8.0 | 3.2 |
| S | 21 | 12 | 4.8 | 6.5 | 2.6 |
| S | 22 | 6 | 9.8 | 11.0 | 4.9 |
| S | 23 | 2 | 12.2 | 12.5 | 6.1 |

## 4. Downtown N, 34 St-Herald Sq (R17) to Canal St bridge level (Q01)

Median scheduled seconds by hour of departure from 34 St. Weekday N runs express; weekend N runs local through 28 St, 23 St, 8 St and Prince St. `local_penalty_s` = Saturday minus Weekday: a first estimate of variant V1's cost per through-rider (weekend schedules carry different padding, so treat as rough).

| hour | Weekday | Saturday | Sunday | local_penalty_s |
|---|---|---|---|---|
| 6 | 390 | 540 | 510 | 150 |
| 7 | 390 | 570 | 540 | 180 |
| 8 | 420 | 570 | 540 | 150 |
| 9 | 390 | 570 | 570 | 180 |
| 10 | 390 | 570 | 570 | 180 |
| 11 | 390 | 570 | 570 | 180 |
| 12 | 390 | 570 | 570 | 180 |
| 13 | 390 | 570 | 570 | 180 |
| 14 | 390 | 570 | 570 | 180 |
| 15 | 405 | 570 | 570 | 165 |
| 16 | 420 | 570 | 570 | 150 |
| 17 | 420 | 570 | 570 | 150 |
| 18 | 420 | 570 | 570 | 150 |
| 19 | 420 | 570 | 540 | 150 |
| 20 | 390 | 570 | 540 | 180 |
| 21 | 390 | 540 | 540 | 150 |
| 22 | 390 | 540 | 540 | 150 |

Trips by service day and whether they stop at 8 St:

| service_id | stops_8st | trips |
|---|---|---|
| Saturday | True | 86 |
| Sunday | True | 86 |
| Weekday | False | 121 |

## 5. Your commute: scheduled in-train minutes, departures 7-10 am

In-train time only; add walking, waiting and (for the N to 14 St) the backtrack.

| leg | service | trips | in_train_min |
|---|---|---|---|
| D 71 St -> W 4 St | Weekday | 24 | 35.9 |
| D 71 St -> W 4 St | Saturday | 15 | 35.5 |
| D 71 St -> W 4 St | Sunday | 15 | 35.5 |
| N 18 Av -> 14 St (then backtrack) | Weekday | 25 | 34.4 |
| N 18 Av -> 14 St (then backtrack) | Saturday | 15 | 36.5 |
| N 18 Av -> 14 St (then backtrack) | Sunday | 15 | 36.3 |
| N 18 Av -> 8 St (weekend local N) | Saturday | 15 | 35.0 |
| N 18 Av -> 8 St (weekend local N) | Sunday | 15 | 34.8 |
| W 18 Av -> 8 St (Sea Beach W trips) | Weekday | 1 | 45.5 |
| R/W 14 St -> 8 St (the backtrack) | Weekday | 25 | 1.5 |
| R/W 14 St -> 8 St (the backtrack) | Saturday | 15 | 1.5 |
| R/W 14 St -> 8 St (the backtrack) | Sunday | 15 | 1.5 |
