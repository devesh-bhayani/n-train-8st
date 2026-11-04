# Natural experiment: the N leaves the Broadway local (Nov 7, 2016)

Daily turnstile counts, weekdays, 8 weeks before and 6 weeks after the change, with the same weeks of 2015 as a no-change comparison year. See the module docstring for the model.

## Average weekday counts per turnstile unit

| group | year | post | units | mean_entries | mean_exits |
|---|---|---|---|---|---|
| control | 2015 | 0 | 14 | 15527.0 | 12557.0 |
| control | 2015 | 1 | 14 | 15493.0 | 12557.0 |
| control | 2016 | 0 | 14 | 15630.0 | 12187.0 |
| control | 2016 | 1 | 14 | 15087.0 | 12112.0 |
| spillover | 2015 | 0 | 2 | 78370.0 | 70019.0 |
| spillover | 2015 | 1 | 2 | 77861.0 | 69270.0 |
| spillover | 2016 | 0 | 2 | 78579.0 | 67249.0 |
| spillover | 2016 | 1 | 2 | 75777.0 | 66938.0 |
| treated | 2015 | 0 | 4 | 18979.0 | 14686.0 |
| treated | 2015 | 1 | 4 | 18892.0 | 14861.0 |
| treated | 2016 | 0 | 4 | 19904.0 | 15066.0 |
| treated | 2016 | 1 | 4 | 18813.0 | 13768.0 |

8 St–NYU, all units (weekday averages):

| year | post | daily_entries | daily_exits |
|---|---|---|---|
| 2015 | 0 | 19182.0 | 13201.0 |
| 2015 | 1 | 19098.0 | 13063.0 |
| 2016 | 0 | 20216.0 | 13725.0 |
| 2016 | 1 | 19056.0 | 12642.0 |

## Triple-difference estimates

Effect of the change on daily counts, in percent (95% confidence interval).
`treated` = 28 St, 23 St, 8 St–NYU, Prince St; `spillover` = W 4 St, 14 St–Union Sq.

| group | outcome | effect_pct | ci_low_pct | ci_high_pct | p_value | n_obs | units |
|---|---|---|---|---|---|---|---|
| treated | log_exits | -9.7 | -12.47 | -6.83 | 0.0 | 2371 | 4 |
| treated | log_entries | -2.63 | -6.15 | 1.03 | 0.17 | 2371 | 4 |
| treated | log_total | -6.15 | -8.64 | -3.6 | 0.0 | 2371 | 4 |
| spillover | log_exits | -1.2 | -3.7 | 1.36 | 0.37 | 2131 | 2 |
| spillover | log_entries | -3.5 | -9.11 | 2.45 | 0.26 | 2131 | 2 |
| spillover | log_total | -2.28 | -5.73 | 1.3 | 0.23 | 2131 | 2 |

## Event study (treated vs control, 2016 minus 2015, entries + exits)

Week 0 = the week of Nov 7, 2016. Week −1 is the reference. Pre-change weeks near zero support the parallel-trends assumption.

| week | effect_pct | ci_low_pct | ci_high_pct |
|---|---|---|---|
| -8 | 2.7 | -2.8 | 8.5 |
| -7 | 4.5 | -0.9 | 10.1 |
| -6 | 2.0 | -0.2 | 4.2 |
| -5 | 3.8 | 0.4 | 7.4 |
| -4 | 0.7 | -2.1 | 3.6 |
| -3 | 1.2 | -2.0 | 4.5 |
| -1 | 0.0 | 0.0 | 0.0 |
| 1 | -4.5 | -7.3 | -1.7 |
| 3 | -4.6 | -9.9 | 1.1 |
| 4 | -2.4 | -7.4 | 2.9 |
