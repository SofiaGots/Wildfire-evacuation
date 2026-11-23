"""Coupling: fire + roads + people together.

One scenario = one random fire (ignition point and wind). The question it answers:
what is the latest moment an alert can go out so that the last car still escapes?
All times are minutes after ignition.
"""

import numpy as np

from . import fire, roads


def run_scenario(seed, fuel, net, src, dst, prep_min, queue_min,
                 cell_m=100, min_per_step=2.0, margin_min=5.0, ignition_m=(500, 6000)):
    """Run one random fire and measure what it does to the escape route.

    fuel        bool grid of vegetation
    net         roads.RoadNet of the village area
    src, dst    positions (in net) of the village node and the safe node
    prep_min    minutes people need to get ready after the alert
    queue_min   minutes the queue of cars needs to leave
    ignition_m  the fire starts between these distances (m) from the village
    """
    n = fuel.shape[0]
    rng = np.random.default_rng(seed)
    ang, r = rng.uniform(0, 2 * np.pi), rng.uniform(*ignition_m) / cell_m
    i = int(np.clip(n / 2 + r * np.sin(ang), 2, n - 3))
    j = int(np.clip(n / 2 + r * np.cos(ang), 2, n - 3))
    wind = fire.WINDS[rng.integers(len(fire.WINDS))]

    arrival = fire.simulate_fire(fuel, (i, j), wind=wind, seed=int(seed))
    cut = fire.cut_times(arrival, net.cell, net.in_grid, min_per_step, margin_min)
    d_star = roads.latest_departure(net.adj, cut, src, dst)    # latest minute the LAST car may leave
    return {
        "seed": seed,
        "ignition": (i, j),
        "wind": wind,
        "cut": cut,
        "d_star": d_star,
        "alert_latest": d_star - prep_min - queue_min,         # latest alert, minutes after ignition
    }


def summarize(results):
    """Shares of scenarios in each outcome class (fractions between 0 and 1)."""
    al = np.array([r["alert_latest"] for r in results])
    return {
        "n": len(al),
        "never_blocked": float(np.isposinf(al).mean()),
        "impossible": float((al < 0).mean()),            # even an alert at ignition is too late
        "within_30": float(((al >= 0) & (al < 30)).mean()),
        "within_60": float(((al >= 0) & (al < 60)).mean()),
    }
