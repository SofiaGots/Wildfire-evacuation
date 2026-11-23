"""People: how many cars leave, how long the queue is, how long an evacuation takes.

Pure Python, no dependencies. All times are in minutes.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Estimate:
    cars: float               # cars that have to leave
    queue_min: float          # minutes for the whole queue to drive off at road capacity
    evac_min: float           # preparation + queue + driving to the danger point
    latest_alert_min: float   # latest alert, in minutes after ignition (negative = already too late)
    feasible: bool            # latest_alert_min >= 0


def cars_to_move(homes, cars_per_home):
    return homes * cars_per_home


def queue_minutes(cars, capacity_per_hour, exits=1):
    """Time for `cars` to pass a road of `capacity_per_hour` cars/hour.

    With several exits the cars are assumed to split evenly between them.
    """
    return cars / (capacity_per_hour * exits) * 60


def evacuation_estimate(homes, cars_per_home, capacity_per_hour, prep_min, travel_min,
                        road_cut_min, exits=1, margin_min=5.0):
    """The two-clocks check for one village and one road.

    T_evac       = prep + queue + travel
    latest alert = T_cut - margin - T_evac       (minutes after ignition)
    """
    cars = cars_to_move(homes, cars_per_home)
    queue_min = queue_minutes(cars, capacity_per_hour, exits)
    evac_min = prep_min + queue_min + travel_min
    latest_alert_min = road_cut_min - margin_min - evac_min
    return Estimate(cars, queue_min, evac_min, latest_alert_min, latest_alert_min >= 0)
