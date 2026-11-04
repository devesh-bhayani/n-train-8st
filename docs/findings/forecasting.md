# Forecasting daily ridership a week ahead

47 stations, 2022-02-01 to 2026-10-22. Test: 2026-09-01 to 2026-10-31. Every model only uses information available 7 days before the day it forecasts.

## Accuracy on the test window (WAPE: total absolute error / total riders)

| model | WAPE_% |
|---|---|
| seasonal naive (last week) | 9.21 |
| LightGBM (global) | 6.96 |
| MSTL (statsforecast, rolling) | 8.24 |
| AutoETS (statsforecast, rolling) | 7.77 |

## What LightGBM relies on (mean |SHAP|, log-riders)

| feature | mean_abs_shap |
|---|---|
| same_dow_mean4 | 0.573 |
| lag7 | 0.162 |
| lag364 | 0.107 |
| lag14 | 0.05 |
| complex_id | 0.048 |
| lag21 | 0.038 |
| roll28 | 0.031 |
| dow | 0.023 |
| precip | 0.019 |
| holiday | 0.017 |
| doy_sin | 0.015 |
| nyu_session | 0.015 |
| covid_trend | 0.013 |
| tmax | 0.007 |
| doy_cos | 0.007 |
| tmin | 0.005 |
| month | 0.003 |
| snow | 0.002 |

## The NYU semester at 8 St–NYU

Average SHAP contribution of the semester flag to the forecast, as a percent change in riders (2025–2026 days). The flag uses approximate semester dates.

| nyu_session | weekday | pct | days |
|---|---|---|---|
| 0 | False | -1.8 | 86 |
| 1 | False | 1.4 | 102 |
| 0 | True | -2.3 | 211 |
| 1 | True | 1.7 | 261 |

## Per station (test window), with 90% conformal interval coverage

| station | mean_daily | wape | coverage |
|---|---|---|---|
| Times Sq-42 St | 140070.6 | 5.6 | 86.5 |
| 34 St-Herald Sq | 77457.0 | 7.0 | 78.8 |
| 14 St-Union Sq | 73962.7 | 6.4 | 86.5 |
| Park Place | 43569.2 | 8.5 | 88.5 |
| W 4 St-Wash Sq | 38697.3 | 5.7 | 92.3 |
| 14 St | 37683.4 | 6.1 | 88.5 |
| Canal St | 36274.4 | 6.9 | 80.8 |
| Broadway-Lafayette St | 33359.5 | 5.6 | 84.6 |
| Atlantic Av-Barclays Ctr | 33164.7 | 8.8 | 82.7 |
| Jay St-MetroTech | 27286.8 | 8.3 | 80.8 |
| 57 St-7 Av | 25865.3 | 6.3 | 84.6 |
| 49 St | 20942.9 | 9.3 | 73.1 |
| Borough Hall | 20300.5 | 7.9 | 75.0 |
| South Ferry | 19865.0 | 8.7 | 80.8 |
| DeKalb Av | 18412.6 | 7.0 | 71.2 |
| 23 St | 14733.1 | 6.8 | 88.5 |
| 8 St-NYU | 13611.2 | 7.7 | 84.6 |
| Canal St | 13552.8 | 6.7 | 94.2 |
| Prince St | 12473.0 | 7.5 | 84.6 |
| Spring St | 12460.1 | 6.5 | 92.3 |
| Astor Pl | 12050.2 | 5.8 | 82.7 |
| 5 Av/59 St | 11758.9 | 9.0 | 92.3 |
| Christopher St-Stonewall | 10525.8 | 7.0 | 100.0 |
| Spring St | 10287.9 | 5.2 | 90.4 |
| 28 St | 9500.8 | 5.9 | 86.5 |

Overall interval coverage: 81.9% (target 90%).
