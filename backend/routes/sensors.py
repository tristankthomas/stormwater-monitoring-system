from fastapi import APIRouter
from database import get_recent_readings, clear_db
from simulator import thresholds
import state

router = APIRouter(prefix="/api")

DEFAULT_THRESHOLDS = {
    "conductivity": 800.0
}


@router.get("/readings")
def get_readings(limit: int = 50):
    # returns historical readings for the time-series chart
    return get_recent_readings(limit)


@router.get("/status")
def get_status():
    # latest snapshot from the sensor loop, used on initial page load
    # (empty until the first cycle completes, the dashboard shows dashes until then)
    return state.latest


@router.get("/thresholds")
def get_thresholds():
    # returns current threshold values for the settings view
    return thresholds


@router.post("/thresholds")
def update_thresholds(conductivity: float):
    # update the shared conductivity threshold at runtime without restarting the server
    # (the clarity threshold is fixed, it is tuned through the camera brightness thresholds)
    thresholds["conductivity"] = conductivity
    return thresholds


@router.post("/thresholds/reset")
def reset_thresholds():
    # reset thresholds back to default values
    thresholds["conductivity"] = DEFAULT_THRESHOLDS["conductivity"]
    return thresholds


@router.delete("/clear")
def clear_all():
    # wipe all readings and events from the database — used to reset before a demo
    clear_db()
    return {"message": "database cleared"}