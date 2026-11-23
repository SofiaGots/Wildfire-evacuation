from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.egress import people

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/wishlist")
async def add_to_wishlist(request: Request):
    data = await request.json()
    print("WISHLIST ITEM:", data)
    return {"received": True}


class EstimateIn(BaseModel):
    """One village, one evacuation road. Defaults follow the Lofou test case (assumptions, not measurements)."""
    homes: int = Field(187, ge=1, le=100_000, description="homes with people to evacuate")
    cars_per_home: float = Field(1.5, gt=0, le=10)
    capacity_per_hour: float = Field(700, gt=0, le=20_000, description="cars per hour on ONE road")
    exits: int = Field(1, ge=1, le=10, description="independent exits; cars are assumed to split evenly")
    prep_min: float = Field(30, ge=0, le=600, description="minutes people need to get ready and leave")
    travel_min: float = Field(28, ge=0, le=600, description="minutes of driving to the most exposed road section")
    road_cut_min: float = Field(60, ge=0, le=1440, description="minutes after ignition until that road is lost")
    margin_min: float = Field(5, ge=0, le=120, description="safety margin before the road is lost")


@app.post("/api/evacuation/estimate")
def estimate_evacuation(p: EstimateIn):
    """The two-clocks check: can the last car pass the danger point before the road is cut?

    T_evac = prep + queue + travel
    latest alert (min after ignition) = T_cut - margin - T_evac
    """
    e = people.evacuation_estimate(
        homes=p.homes, cars_per_home=p.cars_per_home, capacity_per_hour=p.capacity_per_hour,
        prep_min=p.prep_min, travel_min=p.travel_min, road_cut_min=p.road_cut_min,
        exits=p.exits, margin_min=p.margin_min,
    )
    if e.feasible:
        message = (f"Feasible: the alert must go out within {e.latest_alert_min:.0f} min of ignition "
                   f"for the last car to pass before the road is cut.")
    else:
        message = (f"Too late: even an alert at ignition is {-e.latest_alert_min:.0f} min short. "
                   f"Stage the departures, open another exit, or help people leave earlier.")
    return {
        "cars": round(e.cars),
        "queue_min": round(e.queue_min, 1),
        "evac_min": round(e.evac_min, 1),
        "latest_alert_min": round(e.latest_alert_min, 1),
        "feasible": e.feasible,
        "message": message,
    }
