# Phase-averaged ledger (check: pure shifts)

OD `od_weekday_2026_04.parquet`; N trips shifted by [0, 120, 240, 360, 480, 600, 720, 840, 960, 1080] s in both baseline and scenario, results averaged; riders sampled every 300 s with jitter, 5 am–midnight. `se` = standard error of the phase average.

Columns: `net_hours` keeps today's stations; `flex_upper` lets every rider around campus take the cheapest station (upper bound on switching, which overpredicts the weekend switch about tenfold); `flex_calibrated` scales that switching benefit by observed ÷ predicted switching on weekends (difference-in-differences, central estimate); `flex_calibrated_raw` uses the raw weekend shift.

## Base weights

| scenario | net_hours | net_hours_sd_across_offsets | hours_saved | hours_lost | se |
|---|---|---|---|---|---|
| pure_shift_180s | 351.0 | 2,069.0 | 5,243.0 | 5,593.0 | 654.0 |
| pure_shift_60s | 143.0 | 718.0 | 3,431.0 | 3,574.0 | 227.0 |

## Across the 13-cell weight grid

| scenario | cells | cells_saving | best | worst |
|---|---|---|---|---|
| pure_shift_180s | 13 | 0 | 246.0 | 468.0 |
| pure_shift_60s | 13 | 0 | 86.0 | 213.0 |
