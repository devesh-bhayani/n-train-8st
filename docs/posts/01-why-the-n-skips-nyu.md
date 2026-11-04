# Why doesn't the N stop at NYU?

*Draft. Numbers marked ⟨…⟩ are filled in from the scenario ledger before publishing.*

Every weekday, N trains roll through 8 St–NYU without stopping. It's the closest subway
station to NYU's Washington Square campus, and the N stops there every weekend. So why not
on weekdays, and would it help if it did?

I'm an NYU student who commutes from Bensonhurst, so I have a stake in the answer. That's
why I wrote down my assumptions before running the numbers ([pre-registration](../preregistration.md))
and published all the code ([repo](https://github.com/devesh-bhayani/n-train-8st)).

## It's a timetable choice, not a track problem

The Broadway line has four tracks. 8 St–NYU only has platforms on the outer two (the local
tracks), and weekday N trains run on the inner two (express) between 34 St and Canal St.
But just south of Prince St there are crossovers between the local and express tracks, and
every weekend the N uses them: it runs local through 28 St, 23 St, 14 St, 8 St and Prince
St, then crosses over to the Manhattan Bridge.

The weekday N did this too, from 2010 to 2016. On November 7, 2016, when the W came back
as part of the Second Avenue Subway changes, the N went back to running express. The local
stations kept the same number of trains (the W replaced the N), but they lost their
one-seat ride from the N's Brooklyn branch.

## When the N left, people stopped getting off there

Turnstile counts from 2016 show what that cost. Compared with nearby stations on other
lines, and with the same weeks of 2015 as a baseline, **exits at 28 St, 23 St, 8 St–NYU and
Prince St fell by about 10%** (95% confidence interval 7–12%) in the weeks after the change.
Entries barely moved: on the way home you can walk to Union Square and catch the N there.
Arriving is where the one-seat ride matters.

## What it costs everyone else

Making the N stop isn't free. Every N rider passing through would sit through four more
stops (28 St, 23 St, 8 St and Prince St) and merge into the R and W on the local tracks.

To measure that, I built a simulation of every train between 57 St and Canal St, replaying
44 real weekdays of observed train movements from [subwaydata.nyc](https://subwaydata.nyc).
It reproduces the real trains' running times within about 2%. With the N running local:

- **N riders** lose about **3 minutes downtown** and **2 minutes uptown**. Uptown is
  cheaper because today's N has to merge into the R/W stream north of 34 St anyway.
- **R and W riders** lose **7–10 seconds** per trip from the extra trains on their tracks.
- **Q riders** gain **26–38 seconds**, because they no longer have to merge with the N.

## The balance

⟨Ledger headline: net rider-hours per weekday, fixed-station and with riders free to
switch to 8 St, and in how many of the 13 weighting assumptions the answer holds.⟩

## My commute, on real trains

I live between the N at 18 Av and the D at 71 St. Replaying every 2-minute departure from my
door between 6:30 and 10:30 am on 43 real weekdays:

| Route to campus | Median | Slowest 10% |
|---|---|---|
| D to W 4 St | 51.8 min | 59.2 min |
| N, change at Canal for the R/W | 54.8 min | 63.0 min |
| N to 14 St, back down on the R/W | 57.2 min | 66.2 min |
| N to 14 St, walk | 61.5 min | 69.6 min |
| **N one-seat to 8 St (if it stopped)** | **50.1 min** | **57.3 min** |

Two things surprised me. Changing at Canal beats backtracking from 14 St by about 2.5
minutes. And even with a stop at 8 St, the D would still often win for me: the benefit
of the stop is spread across thousands of riders, and it's small for each.

## What would change my mind

- If the crossover between 14 St and 8 St exists, a cheaper variant (express to 14 St,
  then local) costs N riders about half as much.
- If weekday local service is slower than the simulation says, the cost rises.
- If many more riders would switch to 8 St than today's stations suggest, the benefit
  rises.

All of these are testable, and the code is open.
