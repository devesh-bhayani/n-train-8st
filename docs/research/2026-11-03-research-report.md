# Put the N's 8 St–NYU skip on trial

The N skips 8 St–NYU on weekdays because of a 2016 service swap, not because the tracks prevent it. When the W returned on **November 7, 2016** to give Astoria a Broadway local while the Q moved to the Second Avenue Subway, the N went back to running express with the Q between 34 St–Herald Sq and Canal St. On weekends, with no W, it already runs local through 8 St using crossovers just south of Prince St, and it ran that way on weekdays from 2010 to 2016. That track geometry changes the question you are asking. The alternative that has actually been operated is not "add one stop" but "run the N local from 34 St to Canal." That adds **four stops (28 St, 23 St, 8 St, Prince St) and roughly 210 seconds of scheduled midday time** for every N rider passing through. A cheaper two-stop version (about 90 s) needs a crossover between 14 St and 8 St, and no source confirmed one exists. The best method to borrow is Josh Wolk's MIT-licensed "Stop the Stop", the viral case for closing 3 Av on the L. Wolk is a software/data engineer, not a professor. Run his method in reverse. His open data already shows that **closing 8 St–NYU would cost about 2,867 rider-hours every weekday (rank 308 of 356)**. A phased project can do five things:

- fork that pipeline and turn its "timetable cuts" into "timetable adds"
- calibrate it with a SimPy simulation and real-time data
- estimate how riders respond, using route-choice models and causal methods on the 2010 and 2016 natural experiments
- score three scenario families: the N stops at 8 St, a reconfigured express/local pattern, or a Union Square shuttle
- put all three on one multi-metric scorecard

Starting with 8 St and then going system-wide is the right order, as long as the code treats a *segment pattern change*, not a single stop, as the thing being tested. The shuttle faces the steepest bar. Under standard weights, a shuttle every 10 minutes barely beats walking from Union Square. NYU publishes no headways or GTFS feed for its buses, so the data must be collected by you, starting now, because fall-term service ends December 22.

## A 2016 service swap, not the track, keeps the N off 8 St–NYU

The Broadway Line between 34 St and Canal St is a four-track trunk. **8 St–NYU and Prince St have only local side platforms**, and the two express tracks run through the middle, so an express train physically cannot stop there ([Wikipedia: 8 St–NYU](https://en.wikipedia.org/wiki/Eighth_Street%E2%80%93New_York_University_station)). The key piece of track lies just south of Prince St. There, **diamond crossovers connect each local track to its express (Manhattan Bridge) track**. A route-request "punch box" at the south end of the southbound platform lets weekend N and late-night Q trains cross onto the bridge after making local stops ([Wikipedia: Prince Street station](https://en.wikipedia.org/wiki/Prince_Street_station)). A local N therefore stops at Prince St, crosses to the bridge track and continues to Canal St's lower-level Bridge platform, using equipment that is in use every weekend. The weekday skip is a scheduling choice.

| Period | Who stops at 8 St–NYU | N routing in Manhattan |
|---|---|---|
| Weekday daytime | R, W | Express 34 St–Canal St with the Q, via the Manhattan Bridge |
| Weekends | R, N | Local in Manhattan ([MTA N schedule, eff. May 17, 2026](https://www.mta.info/schedules/subway/n-train)) |
| Late nights | N, Q | N makes all stops via the Montague tunnel; Q runs local via the bridge; R is cut back to Whitehall–Bay Ridge ([Wikipedia: N service](https://en.wikipedia.org/wiki/N_%28New_York_City_Subway_service%29)) |

The weekday pattern has flipped four times, each time because of bridge repairs or a reshuffle of the W and Q. Manhattan Bridge reconstruction pushed the N onto local service via the Montague tunnel from about 1986–88 until **February 22, 2004**, when bridge service resumed ([NYC DOT bridge report](https://www.nyc.gov/html/dot/downloads/pdf/bridgerpt06_2.pdf)). The 2010 budget cuts eliminated the W, whose last run was Friday, June 25, 2010, and **from June 28, 2010 the N ran local north of Canal St on weekdays** ([Wikipedia: W service](https://en.wikipedia.org/wiki/W_%28New_York_City_Subway_service%29)). In May 2016 the MTA announced the W's return as part of the Second Avenue Subway changes:

- The Q left Astoria for its new 96 St route, which opened January 1, 2017.
- The W returned as the Astoria local on **November 7, 2016**.
- **The N went back to weekday express between 34 St and Canal St** ([Queens Chronicle](https://www.qchron.com/editions/central/w-train-returning-to-queens-on-nov-7/article_01a18eaa-80e3-11e6-ab01-7b047325acfe.html); [metro.fandom: Route W](https://metro.fandom.com/wiki/Route_W_%28New_York_City_Subway%29)).

| Period | Weekday N in Manhattan | Serves 8 St on weekdays? |
|---|---|---|
| ~1986/88 – Feb 22, 2004 | Local via Montague tunnel (bridge repairs) | Yes |
| Feb 22, 2004 – Jun 25, 2010 | Express via the bridge | No |
| Jun 28, 2010 – Nov 4, 2016 | Local north of Canal St (W eliminated) | Yes |
| Nov 7, 2016 – today | Express 34 St–Canal St (W restored) | No |

The structural logic is simple. Two express services (N, Q) feed the bridge and two locals (R, W) feed Lower Manhattan and the Montague tunnel, which is how the line was built. The express pattern saves through-riders real time. In the weekday GTFS, R/W trains take **270 s from 34 St to 14 St versus 150 s for N/Q**, and **330 s from 14 St to Canal versus 240 s** ([stopthestop-data GTFS](https://github.com/WoshuaJolk/stopthestop-data)). What the record lacks is any weighing of NYU access. The research found:

- **no MTA document comparing "N local + W" with "N express + W"**
- no published trains-per-hour capacity figures for the Broadway local
- no organized advocacy from NYU, Community Board 2 or elected officials for an N stop at 8 St, although the searches covered Reddit and Subchat poorly ([NYC Metro station page](https://nyc-metro.com/en/stations/eighth-streetnew-york-university))

The 2016 decision solved an Astoria problem. Its cost at 8 St appears never to have been measured in public, and that gap is the project's opening.

The strongest case for the status quo:

- Astoria riders already have a one-seat local in the W.
- The express keeps N trips through Manhattan about 3.5 minutes shorter.
- The tightest bottlenecks make planners wary of adding dwell time to the N. These are the shared local section from the 60 St tunnel to 34 St and the DeKalb Av junction in Brooklyn ([NYTIP blog](https://www.nerdynel.me/2019/02/nytip103bwayqb/), an amateur source; [metro.fandom: Route B](https://metro.fandom.com/wiki/Route_B_%28New_York_City_Subway%29)).
- No 2025–2026 service increase touched the N, Q, R or W. The November 2025 weekday boosts went to the A and L ([NY Governor](https://www.governor.ny.gov/news/governor-hochul-announces-mta-increase-weekday-service-and-l-subway-lines-beginning-today)).

## The physically proven change adds four stops, not one

8 St and Prince St sit on the local tracks, and the only confirmed crossovers lie south of Prince St. So the N cannot stop at 8 St alone unless it gets onto the local track somewhere between 34 St and 8 St. The notes confirm that the N already runs on the local tracks with the R and W north of 34 St and switches to the express at Herald Sq. The exact switches at 14 St–Union Sq could not be confirmed, because track-map sites were blocked during the research. That leaves a set of variants with very different costs:

| Variant | Weekday N pattern | Stops added | Scheduled cost per N through-rider | Feasibility |
|---|---|---|---|---|
| **V1 Full local** | Local 34 St → Prince St, crossover to bridge | 28 St, 23 St, 8 St, Prince St (+4) | ≈ +210 s (120 s + 90 s from GTFS segment differences) | **Proven**: weekends today, weekdays 2010–2016 |
| **V2 Express then local** | Express 34 → 14 St, cross to local, stop at 8 St and Prince | 8 St, Prince St (+2) | ≈ +90 s | **Unverified**: needs an express-to-local crossover between 14 St and 8 St |
| **V3 8 St only** | As V2, but pass Prince St without stopping | 8 St (+1) | ≈ 45–60 s | **Doubly unverified**: needs V2's crossover plus nonstop running through a local platform |
| **V4 Q local instead** | Q runs local, N stays express | +4 for Q riders | ≈ +210 s per Q through-rider | Proven for the late-night Q |
| **V5 Hybrid** | N local only in some hours (e.g., midday/evening) | +4 in those hours | As V1, with fewer riders exposed | Proven pattern; a timetable design question |
| **V6 Fix the transfer** | More R/W service, timed transfers, or more W trips to the Sea Beach line | 0 | 0 for N riders | Operational; limited by headways and fleet |

The cost of each added stop has a defensible range:

- NYC's own schedule implies **40–60 s per extra stop at midday (median about 45 s)** across seven express/local pairs.
- Wolk uses **50 s**, with a 20–90 s sweep ([methodology.md](https://github.com/WoshuaJolk/stopthestop-data/blob/main/docs/methodology.md)).
- Alon Levy uses about 45 s for subways ([Pedestrian Observations 2022](https://pedestrianobservations.com/2022/04/20/consolidating-stops-with-irregular-spacing/)).
- A physics check with R160/R211 rates (2.5 mph/s acceleration, 3.0 mph/s braking) gives 11–18 s lost to slowing down and speeding up. Adding a 25–60 s dwell gives **roughly 36–78 s** ([R211](https://en.wikipedia.org/wiki/R211_%28New_York_City_Subway_car%29)).
- Dwells at very busy stations cluster at **50–60 s**, as the MTA found at Grand Central ([MTA SAS FEIS Ch. 5B](https://www.mta.info/document/22126)).

Use **45 s per stop as the base, 35–60 s as the main range, and 20–90 s as the sweep**. For V1 and V2, though, use the measured segment differences (210 s and 90 s), because they already include the MTA's scheduled dwell and padding. A peak-hour N with heavy NYU boardings will dwell longer than the midday average, so the cost side needs a dwell term that varies by time of day rather than a single constant.

The merge question is subtler than it looks. A local N does not add a merge. It moves the existing one from Herald Sq down to Prince St. Trains per hour on the local tracks south of 34 St would equal the N+R+W flow those tracks already carry between 57 St and 34 St. The real risks are:

- longer dwells at the busy local platforms of 14 St, 23 St and 8 St
- delays spreading among three services that share one track
- the northbound N cutting into the R/W stream at the Prince St crossover

The 2010–2016 precedent also ran **without the W**. So it does not prove that the N, R and W can all share the local south of 34 St on weekdays. That inference comes from the dated history, and it is exactly what the simulation must test. V1 would also leave the Q as the only weekday service on the express tracks between 34 St and Canal St.

One item could matter more to you than any scenario. Wikipedia reports that **some rush-hour W trips run past Whitehall St to and from 86 St on the Sea Beach line** ([Wikipedia: W service](https://en.wikipedia.org/wiki/W_%28New_York_City_Subway_service%29)). If those trips run local in Manhattan via the Montague tunnel and stop at 18 Av, they already give a handful of Sea Beach riders a one-seat ride to 8 St–NYU. "Run more of them" then becomes the cheapest option in the V6 family. Neither the routing nor the stop pattern is verified. Check the W trips in the static GTFS `stop_times.txt` first.

## Stop the Stop is the template, run in reverse

The viral post came from **Joshua (Josh) Wolk**. The press describes him as a software engineer (NY Post) or a data engineer (Straus News), and no source calls him a professor. His X post, dated October 1, 2026, read: "I ran a simulation built on 700 million real MTA trips. It said to close the 3rd Avenue L stop." The NY Post story quoted the MTA as saying it "appreciate[s] the creative thinking" ([X post](https://x.com/joshuawolk/status/2105643643440955865); [NY Post via dnyuz](https://dnyuz.com/2026/10/11/software-engineers-viral-plan-to-close-l-trains-3rd-ave-stop-shows-it-would-speed-up-commutes/); [Our Town Downtown](https://www.otdowntown.com/news/data-engineer-to-mta-shut-down-3rd-avenue-subway-stop-on-l-train-FL6278340)). At default settings, skipping 3 Av would save a net **+1,823.8 rider-hours per weekday**, the top result among 356 stops. The result stays positive in **39 of 40** cells of a grid crossing a 20–90 s stop cost with a 1–3x walking penalty ([ranking.csv](https://github.com/WoshuaJolk/stopthestop-data/blob/main/results/ranking.csv)). The code and data are public under the MIT license, so you can fork them ([GitHub: stopthestop-data](https://github.com/WoshuaJolk/stopthestop-data)).

The method is a two-sided ledger. One side is the time saved by everyone riding through the stop. The other is the extra walking by the stop's own riders, multiplied by a walking penalty. The inputs:

- **Demand:** MTA origin-destination (OD) estimates for January–August 2026, about **4.05 million weekday trips** ([README](https://github.com/WoshuaJolk/stopthestop-data/blob/main/README.md); dataset [`28vm-gjqr`](https://data.ny.gov/d/28vm-gjqr)).
- **Supply:** a RAPTOR router (a fast public-transit routing algorithm) over the weekday GTFS (feed 20260826). It allows up to three transfers and samples departures six times an hour, so initial waits and transfer waits are included.
- **Removing a stop:** the stop is deleted from every trip, and downstream riders arrive `stop_cost` seconds earlier for each skipped stop. Wolk ran this at 0, 30 and 70 s and interpolated, with 50 s as the default.
- **Walking:** 1.3 m/s, weighted 2x, with walk distances weighted by Census residents and LODES jobs.

Wolk lists what he leaves out: ridership gained or lost, crowding, reliability, recovered train-hours, weekends, and accessibility in the score ([methodology.md](https://github.com/WoshuaJolk/stopthestop-data/blob/main/docs/methodology.md)).

His dataset gives you a starting result for 8 St–NYU ([ranking.csv](https://github.com/WoshuaJolk/stopthestop-data/blob/main/results/ranking.csv); [timetable_cuts.csv](https://github.com/WoshuaJolk/stopthestop-data/blob/main/results/timetable_cuts.csv)):

- 25,423 weekday users and 53,822 effective R/W through-riders
- closing it would save 728.9 train-hours but add 3,596.2 weighted walking hours
- **net −2,867.2 rider-hours per weekday, rank 308 of 356**
- the station is not ADA-accessible

When riders' extra walk is measured to the next stop on the same line, the net stays negative across the whole grid (−471 h to −5,108 h). Its neighbors score −3,346.7 (Prince St), −2,645.2 (23 St) and −1,426.3 (28 St). Of the residents whose nearest station is 8 St–NYU, 20.3% are enrolled in college or graduate school ([stops.json](https://github.com/WoshuaJolk/stopthestop-data/blob/main/results/stops.json); [demographics.csv](https://github.com/WoshuaJolk/stopthestop-data/blob/main/results/demographics.csv)). A quick consistency check (my arithmetic): 53,822 riders × 50 s ≈ 748 hours, close to the 728.9 reported. For this stop, the full network re-route behaves almost like seconds × through-riders. Read the result carefully, though. It proves 8 St–NYU is among the system's least removable stops for the *R and W*. It does not yet say whether the *N* should also stop there.

Reversing the ledger gives the project's core equation:

- **Benefit** sums, over every OD pair whose best path changes, the weighted change in walk, wait, transfers and in-vehicle time.
- **Cost** is the number of N riders on board through each added stop × the stop cost. Add extra dwell from new boardings, merge and headway effects on the local tracks, and knock-on delay to Q/R/W riders ([methodology.md](https://github.com/WoshuaJolk/stopthestop-data/blob/main/docs/methodology.md)).

Mechanically, Wolk's `timetable_cuts.py` becomes a `timetable_adds.py`. It inserts stop-time rows for the N at the V1 or V2 stations, shifts downstream times by the measured segment difference, and re-routes all OD pairs. Five extensions turn a clone into original work:

1. **The change is a segment, not a stop.** V1 adds four stops and also benefits riders at 23 St, 28 St and Prince St.
2. **Wait time can dominate.** Adding the N raises frequency at 8 St from R+W to N+R+W. The J/Z skip-stop debate taught this lesson: when each stop was served by fewer trains, the longer waits cost riders more than the faster ride saved ([Second Ave Sagas](https://secondavenuesagas.com/2009/01/16/requiem-for-a-z)).
3. **Station-to-station OD hides latent demand.** This is the most important extension. On D days you appear in the data as a 71 St → W 4 St trip, and people who walk from Union Square appear as 14 St trips. An 8 St benefit computed on today's destinations therefore undercounts riders who would *switch* destination. You need a door-to-door layer, using r5py plus OSMnx walks from census origins to NYU buildings.
4. **Measure the stop cost instead of fixing it.** The MBTA spin-off "stahpthestahp" does this with the median observed dwell plus a speed-up/slow-down loss at 1.3 m/s² ([GitHub: stahpthestahp](https://github.com/maxtkc/stahpthestahp)).
5. **Score weekends, summer and accessibility** rather than only reporting them.

## Your D-or-N commute is the persona, not the proof

Your trip makes a good worked example, because you live equidistant from two lines and already switch between them. Home is near 18 Av & 72 St in Bensonhurst, between the N at 18 Av (Sea Beach line) and the D at 71 St (West End line). Your default is the D to W 4 St–Wash Sq, a one-seat ride. When the D is delayed, you ride the N to 14 St–Union Sq and backtrack one stop on the R or W, or walk about 15 minutes. You ride almost every day, including weekends and summer, and you would take the N if it stopped at 8 St. The project's choice model should list every path open to you, and some are worth timing yourself:

| Path | Transfers | Status | What to check |
|---|---|---|---|
| D 71 St → W 4 St, walk | 0 | Today's default | Walk to the buildings you actually use. W 4 St is nearer the west/south core, 8 St nearer the Broadway buildings (walk times unverified) |
| N 18 Av → 14 St, change platforms, R/W south one stop → 8 St | 1 (backtrack) | Today's fallback | Platform change at 14 St (layout unverified); R/W wait and how much it varies |
| N → 14 St, walk ~15 min | 0 (long walk) | Fallback | Measured walk time |
| N → Canal St, up to northbound R/W, two stops → 8 St | 1 (same direction) | Exists; you haven't tried it | Time for the transfer up the stairs; this path avoids backtracking ([Wikipedia: Canal St station](https://en.wikipedia.org/wiki/Canal_Street_station_%28New_York_City_Subway%29)) |
| Rush-hour W from 86 St → 8 St | 0 | **Unverified** | Do these trips exist, stop at 18 Av, and run local in Manhattan? |
| N → 8 St one-seat (V1/V2) | 0 | Scenario | The weekend N already does this, so log it |
| N → 14 St + NYU shuttle | 1 | Hypothetical | No documented Union Sq feeder (next section) |

An illustrative calculation shows how the ledger behaves. It is my arithmetic under stated assumptions, not a result. Suppose today's 14 St backtrack costs:

- a 2-minute platform change
- a 2.5-minute average wait for an R or W
- a 2-minute one-stop ride
- a 5-minute pure transfer penalty

With walking and waiting weighted 2x, the N stopping at 8 St would save about **6.5 clock minutes, or about 16 minutes of weighted ("generalized") time**. The in-vehicle time from Canal St to 8 St on the local is roughly the same as the express ride to 14 St, so it doesn't change the result. V1 costs each through-rider 3.5 minutes, so it breaks even at **about one such beneficiary for every 4–5 N riders passing through**. V2 costs 1.5 minutes and breaks even at about one per 10–11. Sweep the weights (1.5–2.5x) and the transfer penalty (0–15 minutes), and V1's break-even ratio ranges from about 1:2.5 to 1:8, while V2's ranges from about 1:6 to 1:19.

Two lessons follow:

- **The transfer penalty is the parameter that drives the benefit side most, and published values vary widely.** It is 10 minutes in the Edinburgh tram appraisal, 15.2–17.7 minutes in one multimodal study, and 28.8 minutes in Tomhave & Khani ([Edinburgh Tram Inquiry](https://edinburghtraminquiry.org/cec00642726_part2); [Universidad de Chile](https://repositorio.uchile.cl/handle/2250/169339?show=full); [World Transit Research](https://www.worldtransitresearch.info/research/8933)).
- **Most real beneficiaries have a better fallback than your worst one.** The Canal transfer, the D, or a cross-platform change to the R in Brooklyn all beat the 14 St backtrack, so their savings fall below the 16-minute illustration.

That is why the policy case has to rest on aggregate flows, not one commute. NYU reports about **60,525 students in fall 2025**, but that is university-wide, and no Washington Square-only figure was found ([NYU at a Glance](https://www.nyu.edu/about/news-publications/nyu-at-a-glance.html)). The OD data tells you who actually rides. The analysis has three steps:

1. **Size the beneficiary pool.** Filter origins to the Sea Beach (N) and West End (D) stations. Filter destinations to 8 St–NYU (complex 16), W 4 St, 14 St–Union Sq, Prince St and Astor Pl. Group by day of week and hour.
2. **Find the through-riders.** Take every OD pair that crosses the 34 St–Canal segment on Broadway: origins in Brooklyn and at Canal and south, paired with destinations north of 14 St and in Queens, plus the reverse.
3. **Assign paths.** The dataset has no route field, and riders from 18 Av could also take the D or Q. So assign each pair a path with a GTFS shortest-path or logit model. The pairs assigned to the N are the people the added stops would delay ([data.ny.gov OD 2024](https://data.ny.gov/Transportation/MTA-Subway-Origin-Destination-Ridership-Estimate-2/jsu2-fbtj)).

Your own role is a revealed-preference diary. Log weekday and weekend trips, their times, and which path you chose; the weekend N already stops at 8 St. The diary will not prove the case, but it will calibrate the choice model and give the write-up a human face.

## A Union Square shuttle must run every few minutes to matter

NYU's shuttle network is built for residence halls, not subway transfers:

- **Routes:** about seven free routes (A, B, C, E, F, G and the weekend-only W) serving Greenwich Village, the Lower East Side, parts of Chinatown, Stuy Town/Peter Cooper Village and Downtown Brooklyn.
- **Hours:** weekdays 7 a.m. to midnight during the academic year.
- **Eligibility:** riders need an NYU ID.
- **Fall 2026 term:** September 2 to December 22, with no service on Labor Day or Fall Break ([amNY](https://www.amny.com/news/nyu-free-shuttle-bus-service-for-seniors/); [NYU Routes and Schedules](https://www.nyu.edu/life/travel-and-transportation/university-transportation/routes-and-schedules.html)).
- **Tracking:** live positions appear on **Passio GO (agency 1007)**, and the unofficial `PassioGo` Python package can read them. **No NYU shuttle GTFS feed was found** on Transitland or the Mobility Database ([Passio GO NYU](https://passiogo.com/?agency=1007); [PyPI PassioGo](https://pypi.org/project/PassioGo)).

No route is documented as a feeder from 14 St–Union Square to Washington Square. The nearest evidence ([NYU Route F](https://www.nyu.edu/life/travel-and-transportation/university-transportation/routes-and-schedules/route-f.html); [NYU Grossman guide 2020](https://med.nyu.edu/education/md-degree/sites/default/files/nyc-student-guide-2020.pdf); [ITP help](https://itp.nyu.edu/help/?p=4024); [Scribd 2011 Route E](https://www.scribd.com/doc/73635201/RouteEWeekend)):

- Route F's northbound stop moved to 3rd Av & 14th St on September 28, 2026, but it runs away from campus.
- A 2020 NYU guide said Route E linked Washington Square with the Whole Foods on E 14th St.
- One help page says Route A to Tandon runs roughly hourly.
- The only headway on record, a 2011 weekend Route E schedule, shows buses every 20–40 minutes.

A useful Union Square shuttle would be a new route, not more frequent service on an existing one.

Your sense that a 10-minute wait makes no sense holds up in the arithmetic. A shuttle's weighted cost is roughly 2 × (walk to and from the bus) + 2 × (headway ÷ 2) + street ride + transfer penalty. Assume 4 minutes of combined walking, a 5-minute ride (unmeasured; Broadway traffic will vary it) and a 5-minute penalty. That totals **18 + headway** minutes. Simply walking 15 minutes costs 30 at a 2x weight. **At a 10-minute headway the shuttle (28) barely beats walking (30).**

To compete with the R/W backtrack, the shuttle would have to run about as often as the trains, on congested streets. The backtrack carries the same transfer penalty, a wait set by the combined R+W headway (plausibly about 4–5 minutes at peak, unverified) and a 2-minute ride. Fleet size is cycle time ÷ headway, so a 20-minute loop every 5 minutes needs four buses all day (illustrative). The shuttle's realistic niche is narrower:

- riders who cannot manage stairs (8 St–NYU is not ADA-accessible in Wolk's data)
- late evenings, when R/W headways stretch
- bad weather

Shuttle service is also tied to the academic year (summer scope unconfirmed), while you ride year-round.

Because none of this is published, the shuttle becomes the project's original-data module:

- **Logger:** poll Passio GO every 30–60 seconds with the PassioGo package and append positions to Parquet.
- **Metrics:** at the stops nearest 14 St, derive headways, running times, the coefficient of variation of headways (a reliability measure) and the span of service.
- **Schedule check:** compare against the Google Sheets schedules NYU posts for Route E ([NYU Route E](https://www.nyu.edu/life/travel-and-transportation/university-transportation/routes-and-schedules/route-e.html)).
- **Etiquette:** check Passio's terms of use and poll gently.
- **Fieldwork:** add stopwatch observations at Union Square.
- **Benchmark:** compare against Citi Bike trips from Union Square to Washington Square stations, which the public trip files allow ([Citi Bike System Data](https://citibikenyc.com/system-data)).

Start the logger in week one. Fall service has about seven weeks left, and spring term is the next chance to collect data.

## Open data covers demand and service, but not crowding or paths

The MTA's open datasets cover almost every input the ledger needs. Four gaps shape the design:

- OD destinations are modelled, not observed.
- There is no path field.
- Hourly ridership counts only entries.
- **No subway crowding or car-load dataset exists.** Load-weigh data covers only the LIRR ([MTA document 152191](https://mta.info/document/152191)).

| Dataset | ID | What it gives | Caveat | Project use |
|---|---|---|---|---|
| Subway Hourly Ridership: Beginning 2025 | `5wq4-mkjj` | Hourly entries by station complex and fare class | Entries only | Demand profiles, forecasting, causal outcomes ([data.ny.gov](https://data.ny.gov/Transportation/MTA-Subway-Hourly-Ridership-Beginning-2025/5wq4-mkjj)) |
| Subway Hourly Ridership: 2020–2024 | `wujg-7c2s` | Same | Actually starts Feb 2022 | 2022–24 history ([data.ny.gov](https://data.ny.gov/Transportation/MTA-Subway-Hourly-Ridership-2020-2024/wujg-7c2s)) |
| Subway Hourly Ridership: 2017–2019 | ID not captured | Pre-COVID baseline | Unknown whether its complex IDs match later editions | Covers the Second Ave Subway opening ([data.gov](https://catalog-old.data.gov/dataset/mta-subway-hourly-ridership-2017-2019)) |
| Turnstile Usage (yearly; e.g., 2016) | `ekwu-khcy` (2016) | Cumulative counters per turnstile, read about every 4 hours | Counters wrap and reset; no OMNY; start date (believed May 2010) unconfirmed | 2010 and 2016 natural experiments ([data.ny.gov](https://data.ny.gov/Transportation/MTA-Subway-Turnstile-Usage-Data-2016/ekwu-khcy); [cleaning guide](https://medium.com/qri-io/taming-the-mtas-unruly-turnstile-data-c945f5f96ba0)) |
| OD Ridership Estimates | 2021 `rapa-97zv`; 2023 `uhf3-t34z`; 2024 `jsu2-fbtj`; 2025 `y2qv-fytt`; Jan–Aug 2026 `28vm-gjqr` (used by Wolk) | Flows between station complexes by month × day of week × hour | Destination inferred from next tap; monthly averages; fractional values; no path | The ledger's demand ([MTA explainer](https://www.mta.info/article/introducing-subway-origin-destination-ridership-dataset); [data.ny.gov 2025](https://data.ny.gov/Transportation/MTA-Subway-Origin-Destination-Ridership-Estimate-B/y2qv-fytt)) |
| Subway Stations / Complexes / Entrances | `39hk-dx4f` / `5f5g-n3cz` / `i9wp-a4ja` | 8 St–NYU = GTFS R21, station 16, complex 16; entrance locations | Other complex IDs unverified | Joins; starting points for walk times ([data.ny.gov](https://data.ny.gov/Transportation/MTA-Subway-Stations/39hk-dx4f)) |
| Static GTFS (regular and supplemented) | Mobility DB `mdb-511` (supplemented) | Schedules; the supplemented feed adds most planned work for 7 days | Schedule ≠ reality; supplemented feed omits some changes | Scenario editing ([MTA developers](https://www.mta.info/developers); [Google Group](https://groups.google.com/g/mtadeveloperresources/c/14d8DV4hnj4)) |
| GTFS-Realtime (NQRW, BDFM; v2 feeds) | api.mta.info | Live trip updates; **no API key** for subway | v1 retirement in 2027 is reported only by a third-party PR | Your own archive ([api.mta.info](https://api.mta.info/); [PR #38](https://github.com/mobility-solutions-inc/mta-subway-gtfs-rt-proxy/pull/38)) |
| subwaydata.nyc (James Fennell) | — | Per-day CSVs of every trip, with stop times | Schema and start date unverified | Observed run times, dwells, headways ([GitHub](https://github.com/jamespfennell/subwaydata.nyc)) |
| HF `digitalhen/nyc-subway-realtime` | — | 30-second snapshots since April 2026 | Gated access | High-resolution headways ([Hugging Face](https://huggingface.co/datasets/digitalhen/nyc-subway-realtime)) |
| Transitland feed archive | `f-dr5r-nyctsubway` | Older static GTFS versions | Coverage dates unchecked | Historical schedules ([Transitland](https://transit.land/feeds/f-dr5r-nyctsubway)) |
| Customer Journey Metrics | `r7qk-6tcy` (2015–19), `4apg-4kt9` (2020–24), `s4u6-t435` (2025+) | Additional Platform Time and Additional Train Time by line | Line-level only | Reliability; 2016 before/after ([data.ny.gov](https://data.ny.gov/Transportation/MTA-Subway-Customer-Journey-Focused-Metrics-2020-2/4apg-4kt9)) |
| Wait Assessment; Trains Delayed; Delay-Causing Incidents | `62c4-mvcx`; `9zbp-wz3y`; `g937-7k7c` | Regularity, delays, causes | Selected timepoints only | Reliability features ([data.gov](https://catalog.data.gov/dataset/mta-subway-wait-assessment-beginning-2025)) |
| Citi Bike, LODES8, DOT pedestrian counts (`2de2-6x2h`), NYU GeoData | — | First/last mile, work commutes, foot traffic, historical GIS | LODES covers jobs, not students | Shuttle benchmark, station catchments ([LODES8 doc](https://lehd.ces.census.gov/data/lodes/LODES8/LODESTechDoc8.4.pdf); [NYU GeoData](https://geo.nyu.edu/catalog/nyu-2451-34502)) |

Two warnings deserve emphasis:

- **OD destinations are inferred.** The MTA infers each destination from the card's next tap and calls the method "imperfect but reasonable." Short events vanish into the monthly averages ([MTA explainer](https://www.mta.info/article/introducing-subway-origin-destination-ridership-dataset)).
- **The MTA's own historical real-time archive has gaps.** One project found "large swatches of data missing," which is why subwaydata.nyc, the Hugging Face archive and your own logger matter ([ResidentMario/nyc-transit-archive](https://github.com/ResidentMario/nyc-transit-archive)).

### Two dated service flips are ready-made natural experiments

**November 7, 2016 is the cleanest break.** Weekday N service disappeared at 8 St–NYU, Prince St, 23 St and 28 St, while the W returned and the R stayed. The legacy turnstile data covers that date. On weekends the N ran local both before and after, so weekends act as a control within the same station. That makes a **triple-difference design** possible: (weekday − weekend) × (treated − control stations) × (post − pre). Candidate control stations are Astor Pl, W 4 St and 14 St–Union Sq, though riders shift between these nearby stations ([Queens Chronicle](https://www.qchron.com/editions/central/w-train-returning-to-queens-on-nov-7/article_01a18eaa-80e3-11e6-ab01-7b047325acfe.html)). The confounders are concrete and dated:

- The Q left Astoria as part of the same change.
- The Second Avenue Subway opened January 1, 2017.
- NYU's semester calendar drives 8 St demand.

**June 28, 2010 is the mirror image**, with two caveats. The same budget package also eliminated the V and changed other routes, and the change fell in summer. If turnstile coverage starts after that date, this window is lost ([Wikipedia: N service](https://en.wikipedia.org/wiki/N_%28New_York_City_Subway_service%29)).

Turnstiles count people *entering* 8 St, while an N stop mainly helps people *arriving* there. Evening entries on the downtown side are the closest proxy for Brooklyn-bound riders. So check whether 8 St's fare-control areas are separated by direction. That is an unverified hypothesis, but if true it would make the 2016 test much sharper. Line-level Customer Journey metrics for 2015–2019 also cover November 2016, so you can ask whether N, R and W reliability changed when the N left the local tracks.

For the 2020s, the OD data's day-of-week dimension gives a weaker comparison. Compare the share of Sea Beach riders going to 8 St–NYU on weekends (N local) against weekdays. Then subtract the same weekend-versus-weekday difference for West End (D) riders, whose service pattern does not change. Trip purposes differ between weekdays and weekends, so treat the result as suggestive. The Montague tunnel closure (August 2013 to September 2014) is not a clean 8 St experiment, because the N was already local then ([Brooklyn Eagle](https://brooklyneagle.com/articles/2014/09/10/montague-street-tunnel-reopens-monday/)).

## Ten metrics and a parameter grid keep the answer honest

A single "net hours" figure would repeat both Wolk's strength and his blind spots. The project should instead publish a scorecard in which every number appears as a range across a parameter sweep.

| Metric | Definition | Method |
|---|---|---|
| **Net weighted passenger-hours** | Benefits − costs per weekday, by hour, using the weights below | RAPTOR/r5py ledger, checked in the simulation |
| **Through-rider delay** | Delayed N riders × added minutes, plus knock-on delay to Q/R/W | Path assignment + simulation |
| **Access-time savings** | Door-to-door change for riders bound for 8 St, Prince, 23 St, 28 St and NYU buildings | r5py + OSMnx |
| **Transfers avoided** | Daily transfers removed at 14 St and Canal St | Path assignment |
| **Wait and reliability** | Expected wait E(W) = E(H)/2 · (1 + CV²), where H is the headway and CV its coefficient of variation; 90th-percentile journey time; Additional Platform Time | Reconstruction from GTFS-RT ([DDNS 2012](https://emis.univie.ac.at/journals/HOA/DDNS/Volume2012/313518.pdf)) |
| **Crowding proxy** | Assigned load per train vs. capacity; dwell growth | OD assignment + dwell model |
| **Local-track performance** | Delay propagation 34 St–Canal; merge conflicts at Prince St | SimPy, with track blocks as capacity-1 resources |
| **Operator cost** | Added N train-hours; shuttle vehicles = cycle time ÷ headway | Arithmetic from schedules |
| **Equity and accessibility** | Gains and losses by origin area (Astoria, Sea Beach, Village); ADA status; jobs and campus reachable within X minutes | ACS, Wolk demographics, r5py |
| **Robustness** | Share of grid cells where the sign of the result holds (Wolk's 3 Av: 39 of 40) | Parameter sweep |

Add seasonal weighting as an eleventh lens. Annualize with the NYU calendar, because shuttle service and student demand collapse in summer while your trips and the subway schedule do not. The parameter grid should look like this:

| Parameter | Base | Sweep | Evidence |
|---|---|---|---|
| Stop cost | 45 s per stop; 210 s (V1) and 90 s (V2) from GTFS segments | 20–90 s | GTFS-derived 40–60 s; Wolk 50 s; physics 36–78 s |
| Walk weight | 2.0 | 1.5–2.5 | USDOT values out-of-vehicle time at 100% of the wage vs. 50% for in-vehicle time ([USDOT 2016](https://www.transportation.gov/sites/dot.gov/files/docs/Revised%20Departmental%20Guidance%20on%20Valuation%20of%20Travel%20Time%20in%20Economic%20Analysis%20-%20September%202016.pdf)); a UK meta-analysis finds walk and wait ratios "substantially lower than … two" ([Abrantes & Wardman](https://www.worldtransitresearch.info/research/3749)) |
| Wait weight | 2.0 | 1.5–2.5 | The Edinburgh appraisal uses 1.8 |
| Pure transfer penalty | 5 min | 0–15 min, stretch to 30 | Edinburgh 10; 15.2–17.7; Tomhave & Khani 28.8 |
| Walk speed | 1.3 m/s | 1.1–1.4 m/s | Wolk; stahpthestahp |
| Dwell | Linear in boardings and alightings, plus a crowding term | Calibrated | TCQSM form; Puong's MBTA model ([MIT OCW](https://mitocw.ups.edu.ec/courses/civil-and-environmental-engineering/1-258j-public-transportation-systems-spring-2010/lecture-notes/MIT1_258JS10_lec15.pdf)) |

## A lean stack, with each tool tied to one question

The minimal stack is **uv, Parquet + DuckDB + Polars, pandera, GeoPandas, nyct-gtfs, a Makefile, and Streamlit or marimo**, plus the analysis libraries below. Every version cited was current on PyPI as of November 2026 ([PyPI](https://pypi.org/)). Each technique earns its place by answering one specific question:

| Project question | Technique | Minimal choice | Stretch | Avoid or flag |
|---|---|---|---|---|
| Net rider-hours per scenario | Counterfactual GTFS + RAPTOR re-route | Fork Wolk's router; gtfs-kit 13 or Polars for edits | r5py 1.1.7 (needs JDK 21+) + OSMnx for door-to-door | UrbanAccess (last release 2020), Peartree (2021); sources disagree on r5py's matrix class name, so check the docs |
| Transfer waits, bunching, merges | Discrete-event simulation at the train/platform level + Monte Carlo | SimPy 4.1.2 | salabim (animation), Ciw for platform queues | MATSim, SUMO rail, OSRD (overkill); OpenTrack/RailSys (commercial) |
| Dwell vs. boardings | Regression / gradient boosting | statsmodels, LightGBM | SVR, as in the Seoul study | No per-train NYC boarding counts exist |
| Would riders switch from D to N? | Multinomial / path-size logit | Biogeme 3.3.5 | Bi-level model with optimization | PyLogit (unmaintained since 2020) |
| Did the 2016 flip move ridership? | Triple-difference, event study, synthetic control, interrupted time series | pyfixest, CausalPy 0.9 | pysyncon, tfcausalimpact, foundation-model counterfactuals | pycausalimpact (abandoned 2020); DoWhy/EconML mostly overkill |
| Seasonal demand for annual weights | A ladder of forecasting models, simple to complex | Seasonal-naive → statsforecast MSTL → mlforecast + LightGBM + SHAP + MAPIE | Chronos / TimesFM zero-shot; neuralforecast | NeuralProphet (stale); LSTM from scratch; a TFT for one station |
| Which stations behave like 8 St? | Clustering of 168-hour weekly profiles | scikit-learn k-means | tslearn DTW | — |
| Network-wide dependence | Spatio-temporal graph neural network (ST-GNN) | — | BasicTS: STID vs. Graph WaveNet | torch-geometric-temporal (slowing), tsl (stale) |
| Best pattern system-wide | Enumeration → mixed-integer program (MILP) with ε-constraint | PuLP + HiGHS | Pyomo, OR-Tools | Reinforcement learning (no case for a static design) |
| Presentation | Interactive dashboard | Streamlit + pydeck, or marimo | lonboard, Observable | PostGIS server, Spark/Kafka, Great Expectations, DVC |

Sources for the table: [PyPI simpy](https://pypi.org/project/simpy/); [PyPI r5py](https://pypi.org/project/r5py/); [r5py install](https://r5py.readthedocs.io/latest/user-guide/installation/installation.html); [PyPI biogeme](https://pypi.org/project/biogeme/); [PyPI pylogit](https://pypi.org/project/pylogit/); [CausalPy docs](https://causalpy.readthedocs.io/en/latest/); [PyPI pycausalimpact](https://pypi.org/project/pycausalimpact/); [PyPI neuralprophet](https://pypi.org/project/neuralprophet/); [STID arXiv](https://arxiv.org/abs/2208.05233); [PyPI urbanaccess](https://pypi.org/project/urbanaccess/); [PyPI peartree](https://pypi.org/project/peartree/).

Three judgments sit behind the table:

- **Fork Wolk's RAPTOR before reaching for r5py.** It reproduces his numbers exactly and keeps the comparison like-for-like. r5py then adds the door-to-door layer you need for latent demand.
- **Model track blocks as capacity-1 SimPy resources.** Merges and lost throughput are where the hidden cost of a new stop lives. Validate a baseline against observed headways before running any scenario.
- **Keep forecasting in a supporting role.** It does not answer "should the N stop," but it sizes seasonal demand and teaches the modern tools. Use a LightGBM model with an NYU-calendar feature, explained with SHAP and benchmarked against Chronos and TimesFM. Li et al. used foundation models like these to build the no-policy baseline for congestion pricing ([arXiv 2606.17530](https://arxiv.org/pdf/2606.17530)).

A GNN that fails to beat LightGBM is still an honest, portfolio-worthy result.

## Start at 8 St, but build a segment engine for the whole system

Yes, starting with 8 St–NYU and going system-wide later is the right order, for three reasons:

- **8 St has unusually good ground truth.** A weekend N already serves it, and two dated weekday flips exist, so you can validate the model on one station before trusting it on others.
- **Wolk's pipeline already scores every station.** Once `timetable_adds` works for the N, a system-wide "add-a-stop" screen is a loop rather than a rewrite.
- **The expensive methods stay focused.** Simulation, logit and causal work become case studies for the few candidates that survive screening.

Two adjustments make this order work:

- **Define the unit of change as a segment pattern**: a service running local between two crossovers. Keep a hand-built table of which patterns are physically feasible, because GTFS cannot tell you where the switches are.
- **Make every function accept a route, a segment and a station list from day one.**

| Phase (rough timing, my estimate) | Question it answers | New skills | Portfolio artifact |
|---|---|---|---|
| **0. Replicate** (weeks 1–2) | Can I reproduce Wolk's −2,867 h for 8 St? | Reading a real pipeline, GTFS structure, RAPTOR | Forked repo + replication notebook |
| **1. Pipeline & EDA** (weeks 2–4) | What does 8 St demand look like by hour, season and origin (Sea Beach vs. West End)? | uv, DuckDB/Polars, pandera, Socrata API, clustering | `make data` pipeline with schema tests; EDA notebook; station-cluster figure |
| **2. Scenario ledger** (weeks 4–6) | Net rider-hours for V1–V6 across the grid | GTFS editing, counterfactual routing, sensitivity design, r5py/OSMnx | Ledger + heat-map grids; first essay, "Why the N skips NYU" |
| **3. Simulation** (weeks 6–9) | Do merges, dwells and bunching change the answer? | SimPy, Monte Carlo, rebuilding actual train movements from GTFS-RT, calibration | Simulation package, validation plot, Pareto chart |
| **4. Demand & causality** (weeks 9–12) | How many riders switch, and did the 2016 change move ridership? | Biogeme, triple-difference, synthetic control, forecasting + SHAP | Causal notebook; forecasting benchmark table |
| **5. Shuttle + dashboard** (weeks 12–14; logging from week 1) | Is a Union Square shuttle viable, and what is the overall verdict? | API logging, headway analytics, dashboard engineering | Streamlit/marimo dashboard with scenario selector and penalty sliders; final write-up |
| **6. System-wide** (later) | Which local stations skipped by express trains most deserve service? | MILP, ε-constraint Pareto fronts, ST-GNN | System-wide ranking and map |

My working hypotheses, to be tested rather than assumed:

- V2, if the crossover exists, is the variant most likely to pass.
- V1 faces a demanding break-even ratio plus real merge risk.
- Whether the N or the Q should run local depends on which line has the lighter through-load relative to its riders bound for 8 St.
- V6 (better R/W frequency, more Sea Beach W trips) may capture a large share of the benefit at almost no cost to through-riders.
- For able-bodied riders at peak, the trains beat a shuttle outright.

## Check these facts before the first model run

| Unverified item | Why it matters | How to verify |
|---|---|---|
| Crossover between 14 St and 8 St | Decides whether V2/V3 exist (90 s vs. 210 s) | Track maps (Vanshnookenraggen, nycsubway.org); reroute notices |
| Rush-hour W trips to/from 86 St | A possible existing one-seat ride for you | Static GTFS: W trips that touch Sea Beach stop IDs, and their stop sequence |
| Stop IDs R20/R21/R22 and the Canal Bridge platform (Q01?) | Correct GTFS edits | `stops.txt`; 8 St = R21 is already confirmed in `39hk-dx4f` |
| Complex IDs (14 St ≈ 602, W 4 St ≈ 167, Canal ≈ 623, Prince ≈ 17) | OD filters | `39hk-dx4f`, `5f5g-n3cz` |
| R/W headways at 8 St by hour; actual headway variability | Size of the transfer-wait benefit | GTFS `stop_times`; reconstruction from GTFS-RT |
| 14 St platform layout for a northbound N → southbound R/W change | Cost of your fallback path | Station diagram; field check |
| Turnstile coverage start date; whether 8 St's control areas are direction-specific | Whether the 2010 window exists; a sharper 2016 test | First dates and control-area IDs in the turnstile files |
| OD Data Dictionary (columns, averages vs. totals, suppression); whether `28vm-gjqr` is the 2026 edition | Ledger arithmetic | data.ny.gov attachments |
| Current shuttle stop lists, schedules, summer service | Shuttle scenario | NYU route pages, Passio GO |
| r5py matrix class name | Code that runs | Current r5py user manual |

## Conclusion

"Why doesn't the N stop at NYU?" turns out to mean "which Broadway service should run local south of 34 St on weekdays?" The MTA last made that decision in 2016, to fix Astoria's service after the Q left, with no public accounting of what it cost Washington Square. That makes this project new work rather than a replication. Wolk's dataset proves 8 St–NYU is one of the system's most valuable local stops, but nobody has priced the N's absence from it. The analysis also hinges on two facts you can pin down in days rather than months. The first is where the switches are, which decides whether the cost is two stops or four. The second is how heavily riders weigh a transfer, which drives the benefit side. So the first weeks should go to verification, not modelling.

The deeper lesson about method is that adding a stop is not simply removal in reverse. Removing a stop hurts riders the OD data already records at that station. Adding one helps riders the data records somewhere else: at W 4 St, at Union Square, on the D. A faithful reversal of Stop the Stop therefore needs a door-to-door destination-choice layer that Wolk never needed. Building that layer, plus a shuttle dataset no one else has collected, is what turns a fork into a portfolio piece.

## Let's brainstorm

These directions branch from the core project. Each pairs an open question with the skill it would exercise.

| Direction | Open question | Technique / skill |
|---|---|---|
| **"Start the Stop," system-wide** | Rank every local station an express skips by the net value of serving it, with feasibility flags | Generalized `timetable_adds`, segment-pattern enumeration, map dashboard |
| **N or Q: who should be local?** | Is it cheaper, per 8 St beneficiary, to slow down Sea Beach (N) or Brighton/Second Ave (Q) through-riders? | Path assignment by line; scenario comparison |
| **The weekend question, reversed** | Is the weekend N-local pattern itself worth its cost, given 9.4% weekend ridership growth in 2025? ([PCAC](https://pcac.org/report/ridershipreturns/)) | The same ledger on weekend GTFS and OD |
| **Time-of-day hybrids** | Does an N that runs local only midday and evening, matching NYU class-change surges, beat all-day patterns? | Hourly ledger; NYU calendar features |
| **Latent 8 St demand** | How many riders now getting off at W 4 St, Union Square or Astor Pl are really headed for the 8 St area? | Door-to-door r5py + destination-choice logit |
| **A measured NYC stop cost** | What is the observed dwell plus speed-up/slow-down loss per station and hour? | stahpthestahp method applied to GTFS-RT |
| **Reliability before and after 2016** | Did R/W regularity change when the N left the local tracks? | Customer Journey metrics 2015–2019, event study |
| **"N or D right now?"** | Can a live recommender beat your gut on delay days? | GTFS-RT feature pipeline, LightGBM delay model, small web app |
| **A student choice survey** | What transfer penalty do NYU commuters' actual choices reveal? | Survey design, Biogeme estimation (mind privacy) |
| **Citi Bike as the shuttle** | How fast and reliable is Union Sq → Washington Sq by bike, by hour? | Citi Bike trip files, distribution analysis |
| **Advocacy path** | What would a brief ready for the community board look like? | Write-up and visual storytelling, as in Wolk's petition |
| **The MTA's own reasoning** | What did the 2016 Transit Committee staff summary say? | Archive search or a FOIL request |

The first two weeks should verify the decisive facts, start the time-sensitive loggers and reproduce Wolk's numbers before you write a single new model:

| Days (from Tue Nov 3, 2026) | Task | Done when |
|---|---|---|
| 1 | Fork `stopthestop-data`; create a uv environment; run the pipeline | Your run reproduces 8 St–NYU at −2,867.2 h and 3 Av at +1,823.8 h |
| 1–2 | Start two loggers: NQRW GTFS-RT every 30–60 s via nyct-gtfs (GitHub Action or cron → Parquet), and Passio GO agency 1007 vehicle positions via PassioGo | 24 hours of both have landed in Parquet without gaps |
| 3 | Load static GTFS; confirm R20/R21/R22 and the Canal Bridge platform; compute R/W headways at R21 by hour; query W trips that touch Sea Beach stops | You can answer yes or no to "does a one-seat W ride from 18 Av exist?" |
| 4 | Pull track maps; settle the 14 St–8 St crossover question; write the V1–V6 feasibility table | Each variant is marked proven, feasible or impossible, with a source |
| 5–6 | Load OD (`y2qv-fytt`, `28vm-gjqr`) and hourly ridership (`5wq4-mkjj`) into DuckDB; add pandera schemas; read the OD Data Dictionary | `make data` rebuilds the tables from scratch |
| 6–7 (weekend Nov 7–8) | Ride the weekend N to 8 St and log door-to-door times; time the Canal St transfer and the Union Square walk; note shuttle stops near 14 St | Your persona diary has its first five entries |
| 8–9 | EDA: 8 St weekly profile; Sea Beach and West End flows to 8 St, W 4 St and 14 St by hour; weekday vs. weekend shares | A notebook with three publishable charts |
| 10 | Back-of-envelope ledger: break-even ratios across the weight and penalty grid | One heat map you can explain in a sentence |
| 11–12 | Write `timetable_adds.py` for V1, with pytest checks (times stay in order, stop sequences renumbered); re-route with Wolk's RAPTOR | Your first net rider-hours number for V1 |
| 13 | Check legacy turnstile coverage dates and 8 St's control areas; download the 2016 file | Natural-experiment window confirmed or ruled out |
| 14 | Write the README plan and a short "Why the N skips NYU" post based on the first section of this report | Your first public artifact is live |
