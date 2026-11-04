# Phase-averaged ledger

OD `od_weekday_2026_04.parquet`; N trips shifted by [-540, -420, -300, -180, -60, 60, 180, 300, 420, 540] s in both baseline and scenario, results averaged; riders sampled every 180 s with jitter, 5 am–midnight. `se` = standard error of the phase average.

Columns: `net_hours` keeps today's stations; `flex_upper` lets every rider around campus take the cheapest station (upper bound on switching, which overpredicts the weekend switch about tenfold); `flex_calibrated` scales that switching benefit by observed ÷ predicted switching on weekends (difference-in-differences, central estimate); `flex_calibrated_raw` uses the raw weekend shift.

## Base weights

| scenario | net_hours | net_hours_sd_across_offsets | hours_saved | hours_lost | net_hours_flex_upper | net_hours_flex_calibrated | net_hours_flex_calibrated_raw | se |
|---|---|---|---|---|---|---|---|---|
| V1_sim_n_only | 622.0 | 748.0 | 3,299.0 | 3,920.0 | 58.0 | 573.0 | 544.0 | 236.0 |
| V1_sim_no_q | 1,677.0 | 735.0 | 3,296.0 | 4,973.0 | 1,114.0 | 1,629.0 | 1,599.0 | 233.0 |

## Across the 13-cell weight grid

| scenario | cells | cells_saving | cells_saving_flex_upper | cells_saving_flex_calibrated | cells_saving_flex_calibrated_raw | best | worst |
|---|---|---|---|---|---|---|---|
| V1_sim_n_only | 13 | 2 | 7 | 2 | 2 | -208.0 | 1,053.0 |
| V1_sim_no_q | 13 | 0 | 1 | 0 | 0 | 720.0 | 2,111.0 |
