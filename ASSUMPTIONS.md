# Assumptions

Every number in EGRESS-CY that is a guess and not a measurement. Each one must be replaced
by a real source or kept with an honest range. Change a number in code → change it here.

| # | Assumption | Value now | Where | Why it matters | How to improve |
|---|------------|-----------|-------|----------------|----------------|
| 1 | Minutes per fire step | 2.0 | `fire.py` (`min_per_step`) | Scales every fire arrival time | Calibrate against a real fire (e.g. Solea 2025 burned area and times) |
| 2 | Fuel layout | random, 85 % density | `fire.random_fuel` | Fire spread and road cuts | Use real vegetation (CORINE land cover) |
| 3 | Terrain / slope | ignored | `fire.py` | Fire runs much faster uphill | Add elevation (SRTM) |
| 4 | Road classes cars may use | not track, path, service, footway, cycleway, bridleway, steps, pedestrian | `roads.EXCLUDED_CLASSES` | A village connected only by an unpaved road looks cut off | Check each village on a map |
| 5 | Road capacity (cars/hour, one direction) | motorway 1800, trunk 1500, primary 1200, secondary 900, tertiary 700, other 500 | `roads.CAPACITY_PER_HOUR` | Queue time and bottlenecks | Traffic-engineering sources (HCM), lane counts from OSM |
| 6 | Speed on ordinary roads | capped at 40 km/h; motorway and trunk keep their own speed | `roads.SPEED_CAP_KMH` | Free-flow drive time (Lofou was 28 min before the cap) | Compare with real drive times |
| 7 | Mixed-class road (several `highway` values) | smallest capacity counts | `roads.edge_capacity` | Conservative | none needed |
| 8 | Cars per home | 1.5 | `people.py` / API default | Number of cars to move | Census data |
| 9 | Homes in Lofou | 187 | API default | Queue size | Count from OSM buildings or census |
| 10 | Preparation time | 30 min | `people.py` / API default | Largest part of total evacuation time | Evacuation studies, survey |
| 11 | Safety margin | 5 min | `people.py`, `fire.cut_times` | Latest alert | Pick by discussion |
| 12 | Ignition place | random, 0.5–6 km from the village | `coupling.run_scenario` | Which scenarios are tested | Use historical ignition points |
| 13 | Wind | 8 directions, equally likely | `coupling.run_scenario` | Fire direction | Use real wind statistics for the area |
| 14 | Congestion | not modelled (free flow until the queue estimate) | `people.py` | Real travel times are longer | Per-road capacity model in week 2–3 |
| 15 | Destination | one safe place | `coupling.run_scenario` | Could be wrong or itself threatened | Several destinations (`data/villages.csv`) |
