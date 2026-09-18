from fastapi import APIRouter
from database import get_recent_readings, clear_db
from simulator import simulator, compute_pollution_score, thresholds

router = APIRouter(prefix="/api")

DEFAULT_THRESHOLDS = {
    "turbidity": 50.0,
    "conductivity": 800.0
}


@router.get("/readings")
def get_readings(limit: int = 50):
    # returns historical readings for the time-series chart
    return get_recent_readings(limit)


@router.get("/status")
def get_status():
    # snapshot of current sensor state, used on initial page load
    turbidity, conductivity = simulator.read()
    diverter_active = (
        turbidity > thresholds["turbidity"] or
        conductivity > thresholds["conductivity"]
    )
    return {
        "turbidity": turbidity,
        "conductivity": conductivity,
        "diverter_active": diverter_active,
        "pollution_score": compute_pollution_score(turbidity, conductivity),
        "rain_event": simulator.rain_event
    }


@router.get("/thresholds")
def get_thresholds():
    # returns current threshold values for the settings view
    return thresholds


@router.post("/thresholds")
def update_thresholds(turbidity: float, conductivity: float):
    # update shared thresholds at runtime without restarting the server
    thresholds["turbidity"] = turbidity
    thresholds["conductivity"] = conductivity
    return thresholds


@router.post("/thresholds/reset")
def reset_thresholds():
    # reset thresholds back to default values
    thresholds["turbidity"] = DEFAULT_THRESHOLDS["turbidity"]
    thresholds["conductivity"] = DEFAULT_THRESHOLDS["conductivity"]
    return thresholds


@router.delete("/clear")
def clear_all():
    # wipe all readings and events from the database — used to reset before a demo
    clear_db()
    return {"message": "database cleared"}