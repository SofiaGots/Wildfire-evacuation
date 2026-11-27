"""Pictures of the road graph (needs matplotlib and numpy; not imported by the API).

plot_cleaning(G_raw, H_clean, origin, destination)
    left:  the whole cleaned network, coloured by road class, with what the cleaning removed
    right: a zoom on the fastest route from origin to destination

Use it from a notebook:
    from src.egress import roads, viz
    G = roads.load_graph(lat, lon, clean=False)
    H = roads.clean_graph(G)
    fig, info = viz.plot_cleaning(G, H, origin=(lat, lon), destination=(34.68, 32.95))
"""

import math

import networkx as nx
import numpy as np

from . import roads

# colour and line width by road class (the capacities come from roads.CAPACITY_PER_HOUR)
COLORS = {
    "motorway": "#5b2a86", "trunk": "#e6550d", "primary": "#f0a030", "secondary": "#2a9d8f",
    "tertiary": "#1f6f8b", "unclassified": "#8aa1a8", "residential": "#b8c4c8",
}
OTHER_COLOR = "#b8c4c8"
WIDTHS = {
    "motorway": 1.6, "trunk": 1.4, "primary": 1.1, "secondary": 0.8,
    "tertiary": 0.6, "unclassified": 0.35, "residential": 0.3,
}
REMOVED_COLOR = "#e0007a"
ROUTE_COLOR = "#1b9e5a"
BACKGROUND = "#fbfbf9"
DRAW_ORDER = ["residential", "unclassified", "tertiary", "secondary", "primary", "trunk", "motorway"]


def _first_class(highway):
    classes = roads.road_class(highway)
    return classes[0] if classes else "unknown"


def _flat(G, lat0):
    """Node id -> (x, y) in degrees, with x shrunk by cos(latitude) so the map is not stretched."""
    k = math.cos(math.radians(lat0))
    return {n: (d["x"] * k, d["y"]) for n, d in G.nodes(data=True)}


def _pairs(G):
    """One entry per road segment, whatever its direction: {(u, v): highway tag}."""
    out = {}
    for u, v, d in G.edges(data=True):
        out.setdefault((min(u, v), max(u, v)), d.get("highway"))
    return out


def nearest_node(G, lat, lon):
    """Node closest to a (lat, lon) point. Plain numpy, so osmnx is not needed."""
    ids = list(G.nodes)
    ys = np.array([G.nodes[n]["y"] for n in ids])
    xs = np.array([G.nodes[n]["x"] for n in ids]) * math.cos(math.radians(lat))
    return ids[int(np.argmin((ys - lat) ** 2 + (xs - lon * math.cos(math.radians(lat))) ** 2))]


def _minutes(G, route):
    try:
        return nx.path_weight(G, route, "travel_time") / 60
    except (KeyError, nx.NetworkXException):
        return None


def _draw(ax, kept, removed, zoomed):
    from matplotlib.collections import LineCollection

    scale = 2.2 if zoomed else 1.0
    ax.set_facecolor(BACKGROUND)
    by_class = {}
    for seg, cls in kept:
        by_class.setdefault(cls, []).append(seg)
    for cls in DRAW_ORDER + sorted(set(by_class) - set(DRAW_ORDER)):
        if cls in by_class:
            ax.add_collection(LineCollection(
                by_class[cls], colors=COLORS.get(cls, OTHER_COLOR),
                linewidths=WIDTHS.get(cls, 0.3) * scale, zorder=2 + DRAW_ORDER.index(cls) if cls in DRAW_ORDER else 2))
    if removed:
        ax.add_collection(LineCollection(removed, colors=REMOVED_COLOR, linewidths=2.0 if zoomed else 0.9, zorder=20))
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


def plot_cleaning(G_raw, H_clean, origin, destination, out=None, names=("origin", "destination")):
    """Draw the cleaned graph, what was removed, and the fastest route. Returns (figure, info).

    origin, destination: (lat, lon). names: labels for the two points. out: a file path to save a PNG (optional).
    info: route length in km and drive time in minutes before and after the cleaning.
    """
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    lat0 = origin[0]
    xy = _flat(G_raw, lat0)
    kept_pairs = _pairs(H_clean)
    raw_pairs = _pairs(G_raw)
    kept = [((xy[u], xy[v]), _first_class(tag)) for (u, v), tag in kept_pairs.items()]
    removed = [(xy[u], xy[v]) for (u, v) in raw_pairs if (u, v) not in kept_pairs]

    a = nearest_node(H_clean, *origin)
    b = nearest_node(H_clean, *destination)
    route = nx.shortest_path(H_clean, a, b, weight="travel_time")
    raw_route = nx.shortest_path(G_raw, nearest_node(G_raw, *origin), nearest_node(G_raw, *destination), weight="travel_time")
    info = {
        "km": nx.path_weight(H_clean, route, "length") / 1000,
        "minutes_after": _minutes(H_clean, route),
        "minutes_before": _minutes(G_raw, raw_route),
        "same_route": route == raw_route,
        "removed_segments": len(removed),
        "nodes_after": H_clean.number_of_nodes(),
    }

    fig, axes = plt.subplots(1, 2, figsize=(16, 8.2), gridspec_kw={"width_ratios": [1.05, 1]})
    fig.patch.set_facecolor(BACKGROUND)
    px = [xy[n][0] for n in route]
    py = [xy[n][1] for n in route]
    k = math.cos(math.radians(lat0))
    marks = [(names[0], origin), (names[1], destination)]

    # left: everything
    ax = axes[0]
    _draw(ax, kept, removed, zoomed=False)
    xs = [p[0] for seg, _ in kept for p in seg]
    ys = [p[1] for seg, _ in kept for p in seg]
    ax.set_xlim(min(xs), max(xs))
    ax.set_ylim(min(ys), max(ys))
    ax.plot(px, py, color=ROUTE_COLOR, lw=2.2, zorder=30)
    ax.set_title(f"Cleaned road network ({info['nodes_after']:,} intersections)\n"
                 "magenta = removed by the cleaning, green = fastest route", fontsize=12, loc="left")

    # right: zoom on the route
    ax = axes[1]
    _draw(ax, kept, removed, zoomed=True)
    cx, cy = (min(px) + max(px)) / 2, (min(py) + max(py)) / 2
    span = max(max(px) - min(px), max(py) - min(py)) * 0.62
    ax.set_xlim(cx - span * 0.95, cx + span * 0.95)
    ax.set_ylim(cy - span, cy + span)
    ax.plot(px, py, color=ROUTE_COLOR, lw=4, zorder=30, solid_capstyle="round")
    before = f"{info['minutes_before']:.1f} min before cleaning, " if info["minutes_before"] is not None else ""
    ax.set_title(f"Zoom on the route: {info['km']:.1f} km, {before}{info['minutes_after']:.1f} min after "
                 f"({roads.SPEED_CAP_KMH:.0f} km/h cap)", fontsize=12, loc="left")
    for name, (lat, lon) in marks:
        for axis in axes:
            axis.scatter([lon * k], [lat], s=70, c="#111", zorder=40, edgecolor="white")
            axis.annotate(name, (lon * k, lat), xytext=(8, 8), textcoords="offset points",
                          fontsize=11, fontweight="bold", zorder=41)

    handles = [Line2D([0], [0], color=COLORS[c], lw=3,
                      label=f"{c} {roads.CAPACITY_PER_HOUR.get(c, roads.DEFAULT_CAPACITY)} cars/h")
               for c in ["motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential"]]
    handles += [Line2D([0], [0], color=REMOVED_COLOR, lw=3, label="removed by cleaning"),
                Line2D([0], [0], color=ROUTE_COLOR, lw=3, label="fastest route")]
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=10, frameon=False)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    if out:
        fig.savefig(out, dpi=130, facecolor=BACKGROUND)
    return fig, info
