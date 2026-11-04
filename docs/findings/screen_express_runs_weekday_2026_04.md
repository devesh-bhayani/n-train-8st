# System-wide screen: express runs made local

78 scenarios, OD `od_weekday_2026_04.parquet`, departures every 10 min 6 am–11 pm with jitter, fixed stations. Each scenario's route is shifted by [-540, -180, 180, 540] s in both baseline and scenario and the results averaged (phase averaging); `se` is the standard error of that average. `net_hours` uses base weights (2× wait/walk, 5-min transfer); `net_x0` and `net_x15` use 0- and 15-minute transfer penalties. Negative = riders save time. Sorted best first.

6 runs save time by more than two standard errors; 36 cost time by more than two; the other 36 are within noise. Track feasibility is not checked: each row needs a track-map check (crossovers at both ends, platform lengths) before it means anything.

| route | direction | from | to | stops_added | median_added_s | hours_saved | hours_lost | net_hours | se | net_x0 | net_x15 | added_stations |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | S | 96 St | Times Sq-42 St | 5 | 240 | 3,778 | 2,610 | -1,168 | 568 | -444 | -2,393 | 86 St, 79 St, 66 St-Lincoln Center, 59 St-Columbus Circle, 50 St |
| F | S | Forest Hills-71 Av | Jackson Hts-Roosevelt Av | 5 | 270 | 6,230 | 5,146 | -1,084 | 331 | -395 | -2,220 | 67 Av, 63 Dr-Rego Park, Woodhaven Blvd, Grand Av-Newtown, Elmhurst Av |
| 2 | S | 96 St | Times Sq-42 St | 5 | 240 | 4,380 | 3,564 | -816 | 713 | 23 | -2,510 | 86 St, 79 St, 66 St-Lincoln Center, 59 St-Columbus Circle, 50 St |
| 3 | N | Times Sq-42 St | 96 St | 5 | 240 | 1,999 | 1,226 | -772 | 192 | 132 | -2,020 | 50 St, 59 St-Columbus Circle, 66 St-Lincoln Center, 79 St, 86 St |
| E | S | Forest Hills-71 Av | Jackson Hts-Roosevelt Av | 5 | 270 | 5,202 | 4,493 | -709 | 218 | -84 | -2,288 | 67 Av, 63 Dr-Rego Park, Woodhaven Blvd, Grand Av-Newtown, Elmhurst Av |
| 2 | N | Times Sq-42 St | 96 St | 5 | 240 | 3,060 | 2,497 | -563 | 103 | 360 | -2,109 | 50 St, 59 St-Columbus Circle, 66 St-Lincoln Center, 79 St, 86 St |
| N | N | Canal St | 34 St-Herald Sq | 4 | 180 | 2,720 | 2,312 | -408 | 523 | -463 | -543 | Prince St, 8 St-NYU, 23 St, 28 St |
| 5 | N | Brooklyn Bridge-City Hall | 125 St | 14 | 630 | 4,190 | 3,970 | -220 | 402 | 1,302 | -4,109 | Canal St, Spring St, Bleecker St, Astor Pl, 23 St-Baruch College, 28 St, 33 St, 51 St, 68 St-Hunter College, 77 St, 96 St, 103 St, 110 St, 116 St |
| 7X | S | Mets-Willets Point | 74 St-Broadway | 4 | 180 | 1,099 | 965 | -134 | 347 | -116 | -155 | 111 St, 103 St-Corona Plaza, 90 St-Elmhurst Av, 82 St-Jackson Hts |
| 5 | S | 125 St | Brooklyn Bridge-City Hall | 14 | 690 | 4,251 | 4,149 | -102 | 341 | 1,330 | -3,730 | 116 St, 110 St, 103 St, 96 St, 77 St, 68 St-Hunter College, 51 St, 33 St, 28 St, 23 St-Baruch College, Astor Pl, Bleecker St, Spring St, Canal St |
| D | N | W 4 St-Wash Sq | 34 St-Herald Sq | 2 | 90 | 1,812 | 1,745 | -67 | 96 | 215 | -580 | 14 St, 23 St |
| D | S | Grand St | Atlantic Av-Barclays Ctr | 1 | 45 | 730 | 699 | -31 | 49 | -10 | -117 | DeKalb Av |
| FX | N | Queens Plaza | Forest Hills-71 Av | 10 | 570 | 29 | 10 | -19 | 3 | -16 | -42 | 36 St, Steinway St, 46 St, Northern Blvd, 65 St, Elmhurst Av, Grand Av-Newtown, Woodhaven Blvd, 63 Dr-Rego Park, 67 Av |
| FX | S | Forest Hills-71 Av | Jackson Hts-Roosevelt Av | 5 | 270 | 148 | 136 | -12 | 37 | -6 | -34 | 67 Av, 63 Dr-Rego Park, Woodhaven Blvd, Grand Av-Newtown, Elmhurst Av |
| FX | S | Jay St-MetroTech | Church Av | 6 | 300 | 51 | 45 | -7 | 17 | 0 | -12 | Bergen St, Carroll St, Smith-9 Sts, 4 Av-9 St, 15 St-Prospect Park, Fort Hamilton Pkwy |
| Z | N | 104 St | 121 St | 1 | 45 | 11 | 14 | 3 | 3 | 3 | 0 | 111 St |
| Z | N | Crescent St | Woodhaven Blvd | 2 | 90 | 30 | 36 | 5 | 7 | 7 | 2 | Cypress Hills, 85 St-Forest Pkwy |
| Z | N | Van Siclen Av | Norwood Av | 1 | 45 | 18 | 25 | 7 | 4 | 7 | 5 | Cleveland St |
| Z | S | Chauncey St | Marcy Av | 5 | 225 | 150 | 157 | 7 | 30 | 20 | -48 | Halsey St, Kosciuszko St, Flushing Av, Lorimer St, Hewes St |
| B | N | W 4 St-Wash Sq | 34 St-Herald Sq | 2 | 90 | 1,702 | 1,710 | 8 | 140 | 275 | -517 | 14 St, 23 St |
| FX | S | Jackson Hts-Roosevelt Av | Queens Plaza | 5 | 270 | 122 | 132 | 10 | 43 | 13 | 0 | 65 St, Northern Blvd, 46 St, Steinway St, 36 St |
| FX | N | Church Av | Jay St-MetroTech | 6 | 390 | 66 | 80 | 14 | 19 | 15 | 13 | Fort Hamilton Pkwy, 15 St-Prospect Park, 4 Av-9 St, Smith-9 Sts, Carroll St, Bergen St |
| Z | S | Norwood Av | Van Siclen Av | 1 | 45 | 75 | 94 | 19 | 36 | 24 | 12 | Cleveland St |
| Z | S | 121 St | 104 St | 1 | 45 | 77 | 97 | 20 | 28 | 25 | 15 | 111 St |
| Z | S | Woodhaven Blvd | Crescent St | 2 | 90 | 98 | 119 | 21 | 31 | 20 | 18 | 85 St-Forest Pkwy, Cypress Hills |
| Z | N | Marcy Av | Chauncey St | 5 | 225 | 149 | 176 | 27 | 13 | 46 | -25 | Hewes St, Lorimer St, Flushing Av, Kosciuszko St, Halsey St |
| N | S | Canal St | Atlantic Av-Barclays Ctr | 1 | 45 | 743 | 770 | 27 | 17 | 55 | -88 | DeKalb Av |
| 4 | S | Franklin Av-Medgar Evers College | Crown Hts-Utica Av | 2 | 90 | 275 | 333 | 57 | 8 | 180 | -134 | Nostrand Av, Kingston Av |
| 4 | N | Nevins St | Borough Hall | 1 | 90 | 2,552 | 2,613 | 61 | 363 | 17 | 54 | Hoyt St |
| 7X | N | 61 St-Woodside | Mets-Willets Point | 5 | 225 | 992 | 1,118 | 127 | 184 | 154 | 71 | 74 St-Broadway, 82 St-Jackson Hts, 90 St-Elmhurst Av, 103 St-Corona Plaza, 111 St |
| D | N | 36 St | Atlantic Av-Barclays Ctr | 4 | 210 | 3,162 | 3,321 | 159 | 245 | 341 | -333 | 25 St, Prospect Av, 4 Av-9 St, Union St |
| 5 | S | Borough Hall | Nevins St | 1 | 45 | 281 | 449 | 168 | 26 | 218 | 113 | Hoyt St |
| M | S | Broadway-Lafayette St | Delancey St-Essex St | 1 | 45 | 400 | 571 | 170 | 32 | 193 | 76 | 2 Av |
| 4 | N | Crown Hts-Utica Av | Atlantic Av-Barclays Ctr | 5 | 270 | 3,650 | 3,826 | 176 | 665 | 502 | -272 | Kingston Av, Nostrand Av, Eastern Pkwy-Brooklyn Museum, Grand Army Plaza, Bergen St |
| D | S | Atlantic Av-Barclays Ctr | 36 St | 4 | 180 | 1,322 | 1,504 | 182 | 14 | 368 | -227 | Union St, 4 Av-9 St, Prospect Av, 25 St |
| N | S | 34 St-Herald Sq | Canal St | 4 | 210 | 2,087 | 2,310 | 223 | 163 | 238 | 99 | 28 St, 23 St, 8 St-NYU, Prince St |
| 4 | S | Borough Hall | Nevins St | 1 | 45 | 268 | 491 | 223 | 23 | 314 | 130 | Hoyt St |
| N | N | 59 St | Atlantic Av-Barclays Ctr | 6 | 300 | 3,295 | 3,541 | 246 | 318 | 711 | -394 | 53 St, 45 St, 25 St, Prospect Av, 4 Av-9 St, Union St |
| 5 | N | Nevins St | Borough Hall | 1 | 90 | 1,832 | 2,091 | 260 | 382 | 183 | 241 | Hoyt St |
| 4 | N | Brooklyn Bridge-City Hall | 125 St | 14 | 630 | 5,207 | 5,467 | 260 | 319 | 2,015 | -4,045 | Canal St, Spring St, Bleecker St, Astor Pl, 23 St-Baruch College, 28 St, 33 St, 51 St, 68 St-Hunter College, 77 St, 96 St, 103 St, 110 St, 116 St |
| D | N | Atlantic Av-Barclays Ctr | Grand St | 1 | 45 | 1,175 | 1,465 | 290 | 119 | 383 | 155 | DeKalb Av |
| N | N | Atlantic Av-Barclays Ctr | Canal St | 1 | 45 | 953 | 1,246 | 293 | 115 | 389 | 110 | DeKalb Av |
| D | S | 34 St-Herald Sq | W 4 St-Wash Sq | 2 | 150 | 1,771 | 2,097 | 326 | 84 | 657 | -216 | 23 St, 14 St |
| Q | N | Times Sq-42 St | 57 St-7 Av | 1 | 45 | 494 | 864 | 370 | 20 | 507 | 133 | 49 St |
| 3 | S | 34 St-Penn Station | Chambers St | 7 | 315 | 2,026 | 2,450 | 424 | 374 | 933 | -565 | 28 St, 23 St, 18 St, Christopher St-Stonewall, Houston St, Canal St, Franklin St |
| B | S | 34 St-Herald Sq | W 4 St-Wash Sq | 2 | 150 | 1,520 | 1,953 | 433 | 116 | 779 | -165 | 23 St, 14 St |
| Q | N | Canal St | 34 St-Herald Sq | 4 | 180 | 2,386 | 2,840 | 454 | 95 | 434 | 156 | Prince St, 8 St-NYU, 23 St, 28 St |
| N | S | Atlantic Av-Barclays Ctr | 59 St | 6 | 300 | 1,862 | 2,322 | 460 | 54 | 935 | -272 | Union St, 4 Av-9 St, Prospect Av, 25 St, 45 St, 53 St |
| A | N | 14 St | 34 St-Penn Station | 1 | 45 | 975 | 1,454 | 478 | 74 | 665 | 278 | 23 St |
| M | N | Delancey St-Essex St | Broadway-Lafayette St | 1 | 45 | 1,192 | 1,673 | 481 | 107 | 511 | 382 | 2 Av |
| 4 | S | Atlantic Av-Barclays Ctr | Franklin Av-Medgar Evers College | 3 | 180 | 302 | 786 | 484 | 23 | 793 | 97 | Bergen St, Grand Army Plaza, Eastern Pkwy-Brooklyn Museum |
| B | S | Prospect Park | Sheepshead Bay | 8 | 360 | 944 | 1,433 | 489 | 140 | 871 | -23 | Parkside Av, Beverley Rd, Cortelyou Rd, Avenue H, Avenue J, Avenue M, Avenue U, Neck Rd |
| 3 | N | Chambers St | 34 St-Penn Station | 7 | 315 | 2,039 | 2,531 | 492 | 457 | 1,089 | -511 | Franklin St, Canal St, Houston St, Christopher St-Stonewall, 18 St, 23 St, 28 St |
| Q | S | 57 St-7 Av | Times Sq-42 St | 1 | 60 | 1,629 | 2,124 | 495 | 97 | 682 | 274 | 49 St |
| 5 | N | Franklin Av-Medgar Evers College | Atlantic Av-Barclays Ctr | 3 | 135 | 2,464 | 3,018 | 555 | 655 | 684 | 279 | Eastern Pkwy-Brooklyn Museum, Grand Army Plaza, Bergen St |
| 2 | N | Chambers St | 34 St-Penn Station | 7 | 315 | 3,011 | 3,567 | 556 | 416 | 1,134 | -598 | Franklin St, Canal St, Houston St, Christopher St-Stonewall, 18 St, 23 St, 28 St |
| B | N | Sheepshead Bay | Prospect Park | 8 | 360 | 3,253 | 3,831 | 578 | 570 | 946 | 82 | Neck Rd, Avenue U, Avenue M, Avenue J, Avenue H, Cortelyou Rd, Beverley Rd, Parkside Av |
| 5 | S | Atlantic Av-Barclays Ctr | Franklin Av-Medgar Evers College | 3 | 180 | 326 | 919 | 593 | 49 | 672 | 367 | Bergen St, Grand Army Plaza, Eastern Pkwy-Brooklyn Museum |
| A | S | W 4 St-Wash Sq | Canal St | 1 | 60 | 1,264 | 1,886 | 622 | 83 | 786 | 473 | Spring St |
| 2 | S | 34 St-Penn Station | Chambers St | 7 | 315 | 2,216 | 2,910 | 694 | 357 | 1,266 | -527 | 28 St, 23 St, 18 St, Christopher St-Stonewall, Houston St, Canal St, Franklin St |
| E | N | Forest Hills-71 Av | Kew Gardens-Union Tpke | 1 | 90 | 131 | 852 | 721 | 17 | 801 | 623 | 75 Av |
| Q | S | 34 St-Herald Sq | Canal St | 4 | 210 | 2,297 | 3,059 | 762 | 207 | 788 | 557 | 28 St, 23 St, 8 St-NYU, Prince St |
| A | S | 34 St-Penn Station | 14 St | 1 | 45 | 1,313 | 2,169 | 856 | 45 | 1,126 | 579 | 23 St |
| 6X | S | Parkchester | 3 Av-138 St | 9 | 405 | 1,269 | 2,158 | 889 | 634 | 1,067 | 755 | St Lawrence Av, Morrison Av-Soundview, Elder Av, Whitlock Av, Longwood Av, E 149 St, E 143 St-St Mary's St, Cypress Av, Brook Av |
| 4 | S | 125 St | Brooklyn Bridge-City Hall | 14 | 690 | 5,162 | 6,082 | 920 | 412 | 2,692 | -3,464 | 116 St, 110 St, 103 St, 96 St, 77 St, 68 St-Hunter College, 51 St, 33 St, 28 St, 23 St-Baruch College, Astor Pl, Bleecker St, Spring St, Canal St |
| D | N | 59 St-Columbus Circle | 145 St | 8 | 360 | 1,665 | 2,626 | 961 | 157 | 916 | 772 | 72 St, 81 St-Museum of Natural History, 86 St, 96 St, 103 St, Cathedral Pkwy (110 St), 116 St, 135 St |
| E | S | Kew Gardens-Union Tpke | Forest Hills-71 Av | 1 | 60 | 1,391 | 2,359 | 968 | 221 | 1,212 | 813 | 75 Av |
| 6X | N | 3 Av-138 St | Parkchester | 9 | 405 | 427 | 1,401 | 974 | 100 | 1,050 | 781 | Brook Av, Cypress Av, E 143 St-St Mary's St, E 149 St, Longwood Av, Whitlock Av, Elder Av, Morrison Av-Soundview, St Lawrence Av |
| A | N | Canal St | W 4 St-Wash Sq | 1 | 120 | 1,725 | 2,707 | 981 | 195 | 1,095 | 884 | Spring St |
| F | N | Queens Plaza | Forest Hills-71 Av | 10 | 540 | 2,567 | 3,930 | 1,363 | 101 | 1,186 | 146 | 36 St, Steinway St, 46 St, Northern Blvd, 65 St, Elmhurst Av, Grand Av-Newtown, Woodhaven Blvd, 63 Dr-Rego Park, 67 Av |
| D | S | 145 St | 59 St-Columbus Circle | 8 | 360 | 3,120 | 4,503 | 1,383 | 275 | 1,357 | 1,292 | 135 St, 116 St, Cathedral Pkwy (110 St), 103 St, 96 St, 86 St, 81 St-Museum of Natural History, 72 St |
| A | S | Hoyt-Schermerhorn Sts | Euclid Av | 9 | 405 | 2,272 | 4,192 | 1,920 | 208 | 2,200 | 1,481 | Lafayette Av, Clinton-Washington Avs, Franklin Av, Kingston-Throop Avs, Ralph Av, Rockaway Av, Liberty Av, Van Siclen Av, Shepherd Av |
| A | N | 42 St-Port Authority Bus Terminal | 168 St | 11 | 495 | 2,401 | 4,422 | 2,022 | 96 | 2,248 | 1,378 | 50 St, 72 St, 81 St-Museum of Natural History, 86 St, 96 St, 103 St, Cathedral Pkwy (110 St), 116 St, 135 St, 155 St, 163 St-Amsterdam Av |
| E | N | Queens Plaza | Forest Hills-71 Av | 10 | 540 | 3,051 | 5,107 | 2,055 | 66 | 2,420 | 3 | 36 St, Steinway St, 46 St, Northern Blvd, 65 St, Elmhurst Av, Grand Av-Newtown, Woodhaven Blvd, 63 Dr-Rego Park, 67 Av |
| F | S | Jackson Hts-Roosevelt Av | Queens Plaza | 5 | 285 | 3,221 | 5,466 | 2,245 | 227 | 2,169 | 1,759 | 65 St, Northern Blvd, 46 St, Steinway St, 36 St |
| A | N | Euclid Av | Hoyt-Schermerhorn Sts | 9 | 405 | 4,077 | 6,529 | 2,452 | 217 | 2,811 | 2,089 | Shepherd Av, Van Siclen Av, Liberty Av, Rockaway Av, Ralph Av, Kingston-Throop Avs, Franklin Av, Clinton-Washington Avs, Lafayette Av |
| E | S | Jackson Hts-Roosevelt Av | Queens Plaza | 5 | 285 | 2,648 | 5,158 | 2,510 | 142 | 2,638 | 1,752 | 65 St, Northern Blvd, 46 St, Steinway St, 36 St |
| A | S | 168 St | 42 St-Port Authority Bus Terminal | 11 | 495 | 4,221 | 7,474 | 3,254 | 290 | 3,730 | 2,591 | 163 St-Amsterdam Av, 155 St, 135 St, 116 St, Cathedral Pkwy (110 St), 103 St, 96 St, 86 St, 81 St-Museum of Natural History, 72 St, 50 St |

Runtime 5663 s.