"""Checks for the egress package. No internet needed.

Run from the backend folder:   uv run python tests/test_egress.py
(needs numpy and networkx; works with pytest too)
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import networkx as nx
import numpy as np

from src.egress import coupling, fire, people, roads

LAT0, LON0 = 34.8, 32.9      # an arbitrary village position


def grid_graph(half=6, spacing_m=1000, kmh=40):
    """Square grid of roads with the village in the middle, plus a far 'city' node."""
    G = nx.MultiDiGraph()
    dlat = spacing_m / 110_540
    dlon = spacing_m / (111_320 * math.cos(math.radians(LAT0)))
    for a in range(-half, half + 1):
        for b in range(-half, half + 1):
            G.add_node((a, b), y=LAT0 + a * dlat, x=LON0 + b * dlon)
    seconds = spacing_m / (kmh / 3.6)
    for a in range(-half, half + 1):
        for b in range(-half, half + 1):
            for da, db in ((1, 0), (0, 1)):
                if abs(a + da) <= half and abs(b + db) <= half:
                    G.add_edge((a, b), (a + da, b + db), travel_time=seconds)
                    G.add_edge((a + da, b + db), (a, b), travel_time=seconds)
    G.add_node("city", y=LAT0 - 25_000 / 110_540, x=LON0)
    G.add_edge((-half, 0), "city", travel_time=600)
    G.add_edge("city", (-half, 0), travel_time=600)
    return G


def messy_graph():
    """Small graph with every kind of road problem: a track, a one-way trap, fast and slow roads."""
    G = nx.MultiDiGraph()
    for n in "ABCDEFGH":
        G.add_node(n, y=LAT0, x=LON0)

    def road(u, v, hw, kmh, length=1000, both=True):
        G.add_edge(u, v, highway=hw, speed_kph=kmh, length=length, travel_time=length / (kmh / 3.6))
        if both:
            G.add_edge(v, u, highway=hw, speed_kph=kmh, length=length, travel_time=length / (kmh / 3.6))

    road("A", "B", "primary", 80)
    road("B", "C", "secondary", 50)
    road("C", "D", ["residential", "tertiary"], 30)
    road("D", "E", "motorway", 100)
    road("A", "E", "track", 30)                       # a shortcut over an unpaved track
    road("C", "F", "service", 20)                     # a service road to a node nothing else reaches
    road("D", "G", "residential", 30, both=False)     # one-way dead end: G cannot get back out
    G.add_node("H")                                   # no roads at all
    return G


def test_clean_graph_removes_unusable_roads():
    H = roads.clean_graph(messy_graph())
    assert "H" not in H and "F" not in H and "G" not in H      # isolated, service-only, one-way trap
    assert not H.has_edge("A", "E")                            # the track is gone
    assert set(H.nodes) == {"A", "B", "C", "D", "E"}


def test_clean_graph_capacities_and_speeds():
    G = messy_graph()
    H = roads.clean_graph(G)
    assert H["A"]["B"][0]["capacity"] == 1200 and H["B"]["C"][0]["capacity"] == 900
    assert H["C"]["D"][0]["capacity"] == 500                   # mixed classes: the smaller capacity
    assert H["D"]["E"][0]["capacity"] == 1800
    assert H["A"]["B"][0]["speed_kph"] == 40                   # 80 km/h capped to 40
    assert abs(H["A"]["B"][0]["travel_time"] - 1000 / (40 / 3.6)) < 1e-9
    assert H["C"]["D"][0]["speed_kph"] == 30                   # slower roads are not sped up
    assert H["D"]["E"][0]["speed_kph"] == 100                  # motorway keeps its speed
    assert G["A"]["B"][0]["speed_kph"] == 80                   # the input is untouched
    assert G.has_edge("A", "E")


def test_clean_graph_keeps_a_graph_without_tags():
    G = grid_graph(half=2)
    H = roads.clean_graph(G)
    assert len(H.edges) == len(G.edges)                        # nothing is dropped
    assert all(d["capacity"] == roads.DEFAULT_CAPACITY for _, _, d in H.edges(data=True))
    assert H[(0, 0)][(1, 0)][0]["travel_time"] == G[(0, 0)][(1, 0)][0]["travel_time"]   # no length: untouched


def test_people_lofou_numbers():
    e = people.evacuation_estimate(187, 1.5, 700, prep_min=30, travel_min=28, road_cut_min=60)
    assert round(e.queue_min, 2) == 24.04
    assert round(e.evac_min, 2) == 82.04
    assert round(e.latest_alert_min, 2) == -27.04 and not e.feasible
    e2 = people.evacuation_estimate(187, 1.5, 700, prep_min=30, travel_min=28, road_cut_min=120, exits=2)
    assert e2.feasible and round(e2.latest_alert_min) == 45


def test_fire_needs_fuel():
    arrival = fire.simulate_fire(np.zeros((50, 50), bool), (25, 25))
    assert np.isfinite(arrival).sum() == 9            # only the 3x3 ignition patch


def test_fire_goes_with_the_wind():
    fuel = np.ones((101, 101), bool)
    arrival = fire.simulate_fire(fuel, (50, 50), wind=(0, 1))
    assert arrival[50, 75] < arrival[50, 25]          # 25 cells east is reached earlier than 25 cells west


def test_exits_on_a_grid():
    k, cut = roads.village_exits(grid_graph(), LAT0, LON0, inner_m=400, outer_m=5000)
    assert k == 4 and len(cut) == 4                    # the village node has 4 roads


def test_latest_departure():
    G = grid_graph()
    net = roads.build_roadnet(G, LAT0, LON0)
    src, dst = net.idx[(0, 0)], net.idx["city"]
    never = np.full(len(net.nodes), np.inf)
    assert roads.latest_departure(net.adj, never, src, dst) == np.inf
    lost_at_10 = never.copy()
    lost_at_10[src] = 10
    assert abs(roads.latest_departure(net.adj, lost_at_10, src, dst) - 10) < 0.2
    lost_at_0 = never.copy()
    lost_at_0[src] = 0
    assert roads.latest_departure(net.adj, lost_at_0, src, dst) == -np.inf


def test_scenarios_are_repeatable():
    G = grid_graph()
    net = roads.build_roadnet(G, LAT0, LON0)
    src, dst = net.idx[(0, 0)], net.idx["city"]
    fuel = fire.random_fuel(150, 0.85, 1)
    a = coupling.run_scenario(3, fuel, net, src, dst, prep_min=30, queue_min=24)
    b = coupling.run_scenario(3, fuel, net, src, dst, prep_min=30, queue_min=24)
    assert a["ignition"] == b["ignition"] and a["wind"] == b["wind"] and a["d_star"] == b["d_star"]
    s = coupling.summarize([coupling.run_scenario(k, fuel, net, src, dst, 30, 24) for k in range(10)])
    assert s["n"] == 10 and 0 <= s["impossible"] <= 1


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("OK  ", name)
