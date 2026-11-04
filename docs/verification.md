# Fact checks

Status: ✅ verified, ⚠️ partly, ❓ open. Update the evidence column as items close.

| Item | Status | Evidence |
|---|---|---|
| GTFS IDs: 8 St–NYU R21, 14 St R20, Prince R22, Canal local R23, Canal bridge Q01, 18 Av (N) N05, 71 St (D) B17, W 4 St D20 | ✅ | MTA static GTFS, feed valid 2026-11-01 to 2027-05-15 |
| Weekday daytime N/Q never stop at 8 St; weekday N stops there only after ~9 pm and overnight | ✅ | `docs/findings/week1_gtfs_checks.md` §1 |
| Weekend N runs local through 8 St all day | ✅ | same, §1 (149 daytime trips per weekend day) |
| Some weekday W trips run from the Sea Beach line (18 Av) to 8 St | ✅ | §2: 2 northbound (leave 18 Av 07:12 and 16:41), 1 southbound (leaves 8 St 21:06); via Montague tunnel; 45.5 min in-train vs 34.4 min on the N to 14 St |
| Downtown R/W headways at 14 St | ✅ | Scheduled (§3): median 3.5–5 min daytime, expected wait 2.2–2.8 min. Observed (subwaydata.nyc, Sep–Nov 2026): about 3 min average wait in the daytime, 1 gap in 10 longer than 7–9 min (`docs/findings/observed_service.md`) |
| Scheduled cost of V1 (N local 34 St → Canal) | ✅ | Schedule: 150–180 s (§4). Observed: weekday R/W local running implies ~210 s (`docs/findings/observed_service.md`). The calibrated simulation, which includes merging with the R/W, gives 185 s downtown and 110 s uptown (`docs/findings/simulation.md`) |
| Crossover between 14 St and 8 St (decides whether V2 exists) | ❓ | Track maps (nycsubway.org, Vanshnookenraggen); reroute notices |
| MTA complex IDs for the focus stations | ✅ | `make stations` (dataset 39hk-dx4f): 8 St–NYU is complex 16 |
| OD and hourly-ridership column names | ✅ | Recorded by `n8st.data.recon` (mta-data branch, `recon/`); `day_of_week` is a name ("Monday"), `hour_of_day` 0–23; checked again at run time by `socrata.require_columns` |
| Passio system ID 1007 and response shape | ✅ | First GitHub Actions run, 2026-11-03: 4/4 polls ok, 9 buses on 8 routes. NYU's feed sends `paxLoad` and `totalCap` (not `paxLoad100`); parser updated |
| Which shuttle routes connect Union Square and campus | ✅ | `docs/findings/shuttle_first_look.md`: Routes E and W board at 14th St & Irving Pl WB, ~220 m from the subway, next stop 715 Broadway; it's the last leg of a loop via NYU Langone. Route E ran there on Tuesday evening, Nov 3, every 15–30 min (8–16 min expected wait) |
| Stop the Stop reproduces | ✅ | `docs/findings/phase0_wolk_replication.md`: independent re-implementation matches all 356 published stops, 0 rank differences |
| Legacy turnstile coverage start (is June 2010 covered?) | ❓ | Not needed so far: the 2016 study uses the 2015–2017 files (filtered by remote unit, since station names changed in late 2015) |
| 14 St platform layout for northbound N → downtown R/W | ❓ | Station diagram; field check |
| Shuttle logger coverage | ⚠️ | First full evening logged Nov 3 (17:22–21:57 NY); GitHub's hourly schedule skipped five runs, so runs now queue their own successor (Nov 4). Daytime weekday headways still to come |
| Does the weekend N pull riders to 8 St? (validates the switching model) | ✅ | `docs/findings/weekend_experiment.md`: +2.54 points (difference-in-differences vs West End), positive in all nine 2026 months |
