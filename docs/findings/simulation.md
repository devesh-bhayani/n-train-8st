# Broadway line simulation (57 St–7 Av to Canal St)

SimPy, block-signal model, 44 observed weekdays × 3 seeds per scenario, both directions. Trains enter at the times they were observed entering the corridor; scenarios reuse the same entries and random numbers.

Parameters: hold 3 blocks, block target 45 s, base dwell 30 s, 0.12 s per passenger, passenger rates from September 2026 station ridership (rough).

## 1. Validation: simulated vs observed corridor time, baseline, 7 am–8 pm

Seconds from entering the corridor (57 St southbound; Canal northbound) to leaving it.

| direction | route | sim_median | sim_p90 | obs_median | obs_p90 | trips | error_pct |
|---|---|---|---|---|---|---|---|
| N | N | 852.0 | 1005.0 | 855.0 | 1054.0 | 3905 | -0.0 |
| N | Q | 752.0 | 878.0 | 750.0 | 910.0 | 4267 | 0.0 |
| N | R | 958.0 | 1139.0 | 1002.0 | 1240.0 | 4232 | -4.0 |
| N | W | 953.0 | 1130.0 | 1000.0 | 1230.0 | 3147 | -5.0 |
| S | N | 784.0 | 937.0 | 773.0 | 910.0 | 3845 | 1.0 |
| S | Q | 698.0 | 801.0 | 699.0 | 841.0 | 4284 | -0.0 |
| S | R | 922.0 | 1085.0 | 920.0 | 1058.0 | 4235 | 0.0 |
| S | W | 921.0 | 1084.0 | 936.0 | 1070.0 | 3207 | -2.0 |

## 2. What each scenario does to each route (seconds per train, vs baseline)

Same trains, same day, same random numbers. For the N, the delta includes the extra stops themselves; for the R, W and Q it is pure knock-on delay (or relief).

| scenario | direction | route | trains | mean_delta_s | p90_delta_s |
|---|---|---|---|---|---|
| V2 | N | N | 11775 | 95.0 | 269.0 |
| V2 | N | Q | 12804 | 11.0 | 121.0 |
| V2 | N | R | 12726 | 16.0 | 195.0 |
| V2 | N | W | 9495 | 15.0 | 187.0 |
| V2 | S | N | 11586 | 172.0 | 316.0 |
| V2 | S | Q | 12885 | 5.0 | 94.0 |
| V2 | S | R | 12714 | 15.0 | 168.0 |
| V2 | S | W | 9624 | 13.0 | 165.0 |
| V1 | N | N | 11775 | 110.0 | 280.0 |
| V1 | N | Q | 12804 | -38.0 | 55.0 |
| V1 | N | R | 12726 | 10.0 | 175.0 |
| V1 | N | W | 9495 | 9.0 | 169.0 |
| V1 | S | N | 11586 | 185.0 | 340.0 |
| V1 | S | Q | 12885 | -26.0 | 53.0 |
| V1 | S | R | 12714 | 9.0 | 160.0 |
| V1 | S | W | 9624 | 7.0 | 159.0 |

## 3. Service regularity (headway coefficient of variation, local platforms)

| scenario | direction | cv_14st_local | cv_8st |
|---|---|---|---|
| V1 | N | nan | nan |
| V2 | N | nan | nan |
| base | N | nan | nan |
| V1 | S | nan | nan |
| V2 | S | nan | nan |
| base | S | nan | nan |
