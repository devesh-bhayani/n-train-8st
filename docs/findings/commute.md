# Your commute on real trains (weekdays, leaving home 6:30–10:30 am)

43 observed weekdays × a departure every 2 minutes = 5,160 trips per option, replayed on the trains that actually ran (subwaydata.nyc, Sep–Nov 2026). Minutes are door (18 Av & 72 St) to campus.

Assumptions: walk to 71st min 7.0, walk to 18av min 7.0, walk w4 to campus min 5.0, walk 8st to campus min 4.0, walk union sq to campus min 15.0, platform change 14st min 2.0, transfer canal min 3.0.

## Each option

`fastest_share_pct` = how often the option would have been the quickest of the four real ones. N_V1 is hypothetical (the N continuing local from Canal to 8 St).

| option | median_min | mean_min | p90_min | fastest_share_pct |
|---|---|---|---|---|
| D | 51.8 | 53.1 | 59.2 | 63.8 |
| N_backtrack | 57.2 | 61.1 | 66.2 | 6.4 |
| N_canal | 54.8 | 58.4 | 63.0 | 30.1 |
| N_walk | 61.5 | 65.3 | 69.6 | 0.1 |
| N_V1 | 50.1 | 53.8 | 57.3 |  |

## By departure hour (median minutes)

| hour | D_median | N_backtrack_median | N_canal_median | N_V1_median | d_faster_pct |
|---|---|---|---|---|---|
| 6 | 51.4 | 55.9 | 54.1 | 49.0 | 67.9 |
| 7 | 51.6 | 56.9 | 54.4 | 49.8 | 66.3 |
| 8 | 52.7 | 57.5 | 54.7 | 50.3 | 60.4 |
| 9 | 51.4 | 57.2 | 54.8 | 50.3 | 66.3 |
| 10 | 51.7 | 58.3 | 56.4 | 51.4 | 70.9 |

## D or N right now? A LightGBM recommender

Trained on the first 28 weekdays, tested on the last 15 (1,800 departures). It predicts how much faster the D will be than the best N option, from what you can know when leaving: clock time, weekday, weather and the countdown to the next two D and N trains. Mean absolute error 5.6 min.

| strategy | mean_min | p90_min | minutes_lost_vs_oracle |
|---|---|---|---|
| always D | 52.29 | 58.5 | 1.52 |
| always N (best of backtrack/Canal) | 55.65 | 62.28 | 4.88 |
| first train to arrive at home | 51.76 | 57.2 | 0.99 |
| LightGBM recommender | 51.89 | 57.38 | 1.12 |
| oracle (knows the future) | 50.77 | 55.52 | 0.0 |

What drives the prediction (mean |SHAP| in minutes):

| feature | mean_abs_shap_min |
|---|---|
| wait_N_min | 5.38 |
| wait_D_min | 2.88 |
| temp_c | 1.37 |
| gap_N_min | 1.35 |
| hour | 1.25 |
| gap_D_min | 1.09 |
| dow | 0.97 |
| minute | 0.8 |
| precip_mm | 0.11 |
