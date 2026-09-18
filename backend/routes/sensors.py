from fastapi import APIRouter
from database import get_recent_readings
from simulator import simulator, compute_pollution_score, TURBIDITY_THRESHOLD, CONDUCTIVITY_THRESHOLD

router = APIRouter(prefix="/api")


@router.get("/readings")
def get_readings(limit: int = 50):
    # returns historical readings for the time-series chart
    return get_recent_readings(limit)


@router.get("/status")
def get_status():
    # snapshot of current sensor state, used on initial page load
    turbidity, conductivity = simulator.read()
    diverter_active = turbidity > TURBIDITY_THRESHOLD or conductivity > CONDUCTIVITY_THRESHOLD
    return {
        "turbidity": turbidity,
        "conductivity": conductivity,
        "diverter_active": diverter_active,
        "pollution_score": compute_pollution_score(turbidity, conductivity),
        "rain_event": simulator.rain_event
    }
