"""EGRESS: wildfire evacuation analysis for mountain villages.

people.py    how many cars, how long the queue, how long an evacuation takes (pure Python)
fire.py      a simple stochastic fire-spread model on a grid (numpy)
roads.py     the road network as a graph: exits, bottlenecks, time-dependent routing (networkx)
coupling.py  fire + roads + people together: one random fire scenario at a time

The submodules are not imported here on purpose: people.py needs nothing installed,
so the API can use it without numpy, networkx or osmnx.
"""
