# Phase-averaged ledger

OD `od_weekday_2026_04.parquet`; N trips shifted by [-540, -420, -300, -180, -60, 60, 180, 300, 420, 540] s in both baseline and scenario, results averaged; riders sampled every 180 s with jitter, 5 am–midnight. `se` = standard error of the phase average.

Columns: `net_hours` keeps today's stations; `flex_upper` lets every rider around campus take the cheapest station (upper bound on switching, which overpredicts the weekend switch about tenfold); `flex_calibrated` scales that switching benefit by observed ÷ predicted switching on weekends (difference-in-differences, central estimate); `flex_calibrated_raw` uses the raw weekend shift.

## Base weights

| scenario | net_hours | net_hours_sd_across_offsets | hours_saved | hours_lost | net_hours_flex_upper | net_hours_flex_calibrated | net_hours_flex_calibrated_raw | se |
|---|---|---|---|---|---|---|---|---|
| V1_obs | 965.0 | 928.0 | 3,533.0 | 4,498.0 | 447.0 | 920.0 | 893.0 | 293.0 |
| V1_sched | -136.0 | 747.0 | 3,696.0 | 3,561.0 | -700.0 | -184.0 | -214.0 | 236.0 |
| V1_sim | 928.0 | 736.0 | 4,276.0 | 5,204.0 | 366.0 | 880.0 | 851.0 | 233.0 |
| V2_obs | 1,089.0 | 640.0 | 2,248.0 | 3,337.0 | 506.0 | 1,039.0 | 1,009.0 | 202.0 |
| V2_sched | -7.0 | 416.0 | 2,428.0 | 2,421.0 | -619.0 | -60.0 | -92.0 | 132.0 |

## Across the 13-cell weight grid

| scenario | cells | cells_saving | cells_saving_flex_upper | cells_saving_flex_calibrated | cells_saving_flex_calibrated_raw | best | worst |
|---|---|---|---|---|---|---|---|
| V1_obs | 13 | 0 | 4 | 0 | 0 | 320.0 | 1,308.0 |
| V1_sched | 13 | 9 | 12 | 10 | 10 | -895.0 | 371.0 |
| V1_sim | 13 | 1 | 6 | 1 | 1 | -1.0 | 1,355.0 |
| V2_obs | 13 | 0 | 2 | 0 | 0 | 597.0 | 1,332.0 |
| V2_sched | 13 | 9 | 13 | 9 | 9 | -358.0 | 259.0 |
