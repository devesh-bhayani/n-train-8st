# Phase-averaged ledger (check: pure shifts)

OD `od_weekday_2026_04.parquet`; N trips shifted by [0, 60, 120, 180, 240, 300, 360, 420, 480, 540] s in both baseline and scenario, results averaged; riders sampled every 300 s with jitter, 5 am–midnight.

## Base weights

| scenario | net_hours | net_hours_sd_across_offsets | hours_saved | hours_lost |
|---|---|---|---|---|
| pure_shift_180s | 444.0 | 2,602.0 | 5,277.0 | 5,721.0 |
| pure_shift_60s | 258.0 | 1,072.0 | 3,374.0 | 3,632.0 |

## Across the 13-cell weight grid

| scenario | cells | cells_saving | best | worst |
|---|---|---|---|---|
| pure_shift_180s | 13 | 0 | 335.0 | 561.0 |
| pure_shift_60s | 13 | 0 | 186.0 | 326.0 |
