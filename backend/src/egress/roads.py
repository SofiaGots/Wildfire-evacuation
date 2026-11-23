"""Roads: the road network as a graph.

Exits and bottlenecks, driving times, and routing when roads are lost over time.
Needs numpy and networkx. osmnx is imported only inside the two functions that
download data, so everything else works (and can be tested) without it.
Times are in minutes.
"""

import heapq
import math
from dataclasses import dataclass

import networkx as nx
import numpy as np


# ---------- getting the graph ----------

def load_graph(lat, lon, dist=18000, network_type="drive"):
    """Download the road graph around a point from OpenStreetMap (needs osmnx and internet)."""
    import osmnx as ox
    G = ox.graph_from_point((lat, lon), dist=dist, network_type=network_type)
    G = ox.routing.add_edge_speeds(G)
    G = ox.routing.add_edge_travel_times(G)
    return G


def nearest_node(G, lat, lon):
    """Road node closest to a coordinate (needs osmnx)."""
    import osmnx as ox
    return ox.distance.nearest_nodes(G, X=lon, Y=lat)


def drive_minutes(G, a, b):
    """Free-flow driving time along the fastest route from node a to node b."""
    route = nx.shortest_path(G, a, b, weight="travel_time")
    return nx.path_weight(G, route, "travel_time") / 60


# ---------- geometry ----------

def haversine_m(lat1, lon1, lat2, lon2):
    """Distance in metres between two coordinates."""
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def to_cell(lat, lon, lat0, lon0, n_grid=150, cell_m=100):
    """Coordinate -> (i, j) cell of the fire grid, with (lat0, lon0) in the middle. i = north, j = east."""
    x = (lon - lon0) * 111_320 * math.cos(math.radians(lat0))   # metres east
    y = (lat - lat0) * 110_540                                   # metres north
    return int(round(n_grid / 2 + y / cell_m)), int(round(n_grid / 2 + x / cell_m))


# ---------- exits (baseline: every road counts as capacity 1) ----------

def village_exits(G, lat0, lon0, inner_m=400, outer_m=5000):
    """How many separate roads lead out of a village, and which ones.

    Everything within inner_m of the village is the source, everything beyond outer_m the sink.
    Returns (number of exits, set of bottleneck edges).
    """
    U = nx.Graph(G.to_undirected())
    inside = [n for n, d in U.nodes(data=True) if haversine_m(lat0, lon0, d["y"], d["x"]) < inner_m]
    outside = [n for n, d in U.nodes(data=True) if haversine_m(lat0, lon0, d["y"], d["x"]) > outer_m]

    H = U.copy()
    nx.set_edge_attributes(H, 1, "cap")                        # every road = capacity 1
    H.add_edges_from([("SRC", n) for n in inside], cap=10**6)
    H.add_edges_from([(n, "SINK") for n in outside], cap=10**6)

    k, (S, T) = nx.minimum_cut(H, "SRC", "SINK", capacity="cap")
    cut = {(u, v) for u in S for v in H[u] if v in T and "SRC" not in (u, v) and "SINK" not in (u, v)}
    return k, cut


# ---------- routing while roads are being lost ----------

@dataclass
class RoadNet:
    """The graph as plain lists and arrays, for fast repeated routing."""
    nodes: list            # OSM node ids
    idx: dict              # OSM node id -> position in the lists below
    cell: np.ndarray       # (n, 2) fire-grid cell of every node
    in_grid: np.ndarray    # (n,) bool: node lies inside the fire grid
    adj: list              # adj[k] = [(neighbour position, driving minutes), ...], directed


def build_roadnet(G, lat0, lon0, n_grid=150, cell_m=100):
    """Turn a graph with `travel_time` (seconds) on its edges into a RoadNet."""
    nodes = list(G.nodes)
    idx = {n: k for k, n in enumerate(nodes)}
    cell = np.array([to_cell(G.nodes[n]["y"], G.nodes[n]["x"], lat0, lon0, n_grid, cell_m) for n in nodes])
    in_grid = (cell[:, 0] >= 0) & (cell[:, 0] < n_grid) & (cell[:, 1] >= 0) & (cell[:, 1] < n_grid)
    adj = [[] for _ in nodes]
    for u, v, d in G.edges(data=True):                         # directed: one-way roads are respected
        adj[idx[u]].append((idx[v], d["travel_time"] / 60))
    return RoadNet(nodes, idx, cell, in_grid, adj)


def reachable(adj, depart, cut, a, b):
    """Can a car leaving node a at minute `depart` reach node b?

    A car may only enter a node if it gets there before that node's cut time (cut[v]).
    This is Dijkstra's shortest-path algorithm with that one extra rule.
    """
    if depart >= cut[a]:
        return False
    best = {a: depart}
    heap = [(depart, a)]
    while heap:
        tm, u = heapq.heappop(heap)
        if u == b:
            return True
        if tm > best.get(u, np.inf):
            continue
        for v, w in adj[u]:
            tv = tm + w
            if tv < cut[v] and tv < best.get(v, np.inf):
                best[v] = tv
                heapq.heappush(heap, (tv, v))
    return False


def latest_departure(adj, cut, a, b, hi=600):
    """Latest minute (after ignition) a car can leave a and still reach b.

    -inf: the route is already blocked at ignition.  +inf: the fire never blocks it.
    Leaving later can only make things worse, so a binary search finds the boundary.
    """
    if not reachable(adj, 0, cut, a, b):
        return -np.inf
    if reachable(adj, hi, cut, a, b):
        return np.inf
    lo = 0.0
    for _ in range(12):
        mid = (lo + hi) / 2
        if reachable(adj, mid, cut, a, b):
            lo = mid
        else:
            hi = mid
    return lo
