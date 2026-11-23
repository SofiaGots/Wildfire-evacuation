"""Fire: a simple stochastic fire-spread model on a grid.

A grid is a 2-D numpy array. Cell (i, j): i grows to the north, j grows to the east.
Time is measured in simulation steps; coupling.py converts steps to minutes.
"""

import numpy as np

# the 8 compass directions as (di, dj): (1, 0) = wind blows north, (0, 1) = east, ...
WINDS = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]


def random_fuel(n=150, density=0.85, seed=1):
    """Placeholder fuel map: every cell has vegetation with probability `density`.

    To be replaced by real land cover later.
    """
    return np.random.default_rng(seed).random((n, n)) < density


def shift(a, di, dj):
    """Shift an array by (di, dj) without wrapping around the edge."""
    out = np.zeros_like(a)
    h, w = a.shape
    out[max(di, 0):h + min(di, 0), max(dj, 0):w + min(dj, 0)] = \
        a[max(-di, 0):h + min(-di, 0), max(-dj, 0):w + min(-dj, 0)]
    return out


def simulate_fire(fuel, start, wind=(0, 1), base=0.7, wind_k=0.25, steps=600, seed=0):
    """Spread a fire over the grid.

    fuel   bool grid, True where there is vegetation
    start  ignition cell (i, j)
    wind   direction the wind blows towards, e.g. (0, 1) = east
    Returns the step at which the fire arrives in every cell (inf = never burned).
    """
    rng = np.random.default_rng(seed)
    w = np.array(wind, float)
    if np.linalg.norm(w) > 0:
        w /= np.linalg.norm(w)
    state = np.zeros(fuel.shape, np.int8)        # 0 unburnt, 1 burning, 2 burnt
    arrival = np.full(fuel.shape, np.inf)
    i, j = start
    state[i - 1:i + 2, j - 1:j + 2] = 1          # ignite a 3x3 patch
    arrival[i - 1:i + 2, j - 1:j + 2] = 0
    for step in range(1, steps):
        burning = state == 1
        if not burning.any():
            break                                # the fire went out
        new = np.zeros_like(burning)
        for d in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            p = base + wind_k * np.dot(d, w)     # with the wind 0.95, against 0.45, sideways 0.7
            new |= shift(burning, *d) & (rng.random(fuel.shape) < p)
        new &= fuel & (state == 0)
        state[burning] = 2
        state[new] = 1
        arrival[new] = step
    return arrival


def buffer_min(arr, r=1):
    """Earliest fire arrival within r cells of every cell.

    Roads usually run through cells without fuel, which never burn in the model,
    so a road is treated as reached when the fire reaches the cells next to it.
    """
    padded = np.pad(arr, r, constant_values=np.inf)
    out = np.full_like(arr, np.inf)
    for di in range(-r, r + 1):
        for dj in range(-r, r + 1):
            out = np.minimum(out, padded[r + di:r + di + arr.shape[0], r + dj:r + dj + arr.shape[1]])
    return out


def cut_times(arrival, cells, in_grid, min_per_step=2.0, margin_min=5.0):
    """Minute (after ignition) at which every road node is lost; inf = never.

    arrival       fire arrival step per grid cell (from simulate_fire)
    cells         (n_nodes, 2) array: grid cell of every road node
    in_grid       bool array: which nodes lie inside the grid
    min_per_step  minutes of real time per simulation step (an assumption)
    margin_min    a node counts as lost this many minutes before the fire arrives
    """
    reach = buffer_min(arrival) * min_per_step
    cut = np.full(len(cells), np.inf)
    cut[in_grid] = reach[cells[in_grid, 0], cells[in_grid, 1]]
    return cut - margin_min
