# Fact checks

Status: ✅ verified, ⚠️ partly, ❓ open. Update the evidence column as items close.

| Item | Status | Evidence |
|---|---|---|
| GTFS IDs: 8 St–NYU R21, 14 St R20, Prince R22, Canal local R23, Canal bridge Q01, 18 Av (N) N05, 71 St (D) B17, W 4 St D20 | ✅ | MTA static GTFS, feed valid 2026-11-01 to 2027-05-15 |
| Weekday daytime N/Q never stop at 8 St; weekday N stops there only after ~9 pm and overnight | ✅ | `docs/findings/week1_gtfs_checks.md` §1 |
| Weekend N runs local through 8 St all day | ✅ | same, §1 (149 daytime trips per weekend day) |
| Some weekday W trips run from the Sea Beach line (18 Av) to 8 St | ✅ | §2: 2 northbound (leave 18 Av 07:12 and 16:41), 1 southbound (leaves 8 St 21:06); via Montague tunnel; 45.5 min in-train vs 34.4 min on the N to 14 St |
| Scheduled downtown R/W headways at 14 St | ✅ (scheduled) | §3: median 3.5–5 min daytime, expected wait 2.2–2.8 min; 5–6 min after 10 pm. Observed headways still needed (GTFS-RT) |
| Scheduled cost of V1 (N local 34 St → Canal) | ⚠️ | §4: 150–180 s (Saturday local minus weekday express). The report's 210 s used R/W segment differences. Weekend padding differs, so confirm with observed run times |
| Crossover between 14 St and 8 St (decides whether V2 exists) | ❓ | Track maps (nycsubway.org, Vanshnookenraggen); reroute notices |
| MTA complex IDs for the focus stations | ❓ | Resolved automatically by `make stations` from dataset 39hk-dx4f |
| OD and hourly-ridership column names | ❓ | Checked at run time by `n8st.data.socrata.require_columns` |
| Passio system ID 1007 and response shape | ✅ | First GitHub Actions run, 2026-11-03: 4/4 polls ok, 9 buses on 8 routes. NYU's feed sends `paxLoad` and `totalCap` (not `paxLoad100`); parser updated |
| Which shuttle routes connect Union Square and campus | ✅ | `docs/findings/shuttle_first_look.md`: Routes E and W (weekends) board at 14th St & Irving Pl WB, ~220 m from the subway, next stop 715 Broadway; it's the last leg of a loop via NYU Langone |
| Stop the Stop reproduces | ✅ | `docs/findings/phase0_wolk_replication.md`: independent re-implementation matches all 356 published stops, 0 rank differences |
| Legacy turnstile coverage start (is June 2010 covered?) | ❓ | First dates in the turnstile files |
| 14 St platform layout for northbound N → downtown R/W | ❓ | Station diagram; field check |
