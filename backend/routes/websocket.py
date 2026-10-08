import asyncio
import json
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from database import insert_reading, insert_event
from simulator import simulator, compute_pollution_score, thresholds
from camera import camera
import state

router = APIRouter()


class ConnectionManager:
    # manages active websocket connections for live broadcasting
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        # push to all connected clients, silently drop dead connections
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(data))
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


def clarity_class(index: float) -> str:
    # same boundaries the camera uses: 0 = clear, below 1 = moderate, 1 or more = high
    if index <= 0:
        return "clear"
    if index < 1:
        return "moderate"
    return "high"


def read_clarity(cam: dict) -> tuple[float, str]:
    # prefer the real camera, fall back to a simulated value when it is unavailable
    # or has not produced its first frame yet
    if cam.get("available") and cam.get("clarity_index") is not None:
        return cam["clarity_index"], "camera"
    return simulator.simulated_clarity(), "simulated"


def breach_reasons(clarity: float, clarity_source: str, cam: dict, conductivity: float) -> list[str]:
    # one human readable reason per threshold that is currently exceeded,
    # including where the reading came from so simulated data is never mistaken for real
    reasons = []
    if conductivity > thresholds["conductivity"]:
        reasons.append(
            f"Conductivity {conductivity} ppm exceeded {thresholds['conductivity']} ppm "
            f"({simulator.conductivity_source})"
        )
    if clarity >= thresholds["clarity"]:
        if clarity_source == "camera":
            reasons.append(f"Camera classed the water as high turbidity (brightness {cam.get('brightness')})")
        else:
            reasons.append(f"Clarity index {clarity} reached {thresholds['clarity']} (simulated)")
    return reasons


async def sensor_loop():
    # runs continuously in background, reading sensors and broadcasting every 2 seconds
    diverter_was_active = False
    active_since = None

    while True:
        # the real conductivity read blocks for ~0.25s, so run it in a thread
        # to keep the event loop (websocket, camera stream) responsive
        conductivity = await asyncio.to_thread(simulator.read_conductivity)
        cam = camera.get_analysis()
        clarity, clarity_source = read_clarity(cam)

        # the diverter follows the combined score: it activates only when the score is HIGH
        score_value, score_level = compute_pollution_score(clarity, conductivity)
        diverter_active = score_level == "high"

        reasons = breach_reasons(clarity, clarity_source, cam, conductivity)
        if diverter_active and not reasons:
            # neither signal is over its own limit, the combination pushed the score over
            reasons = [
                f"Combined score {score_value}: conductivity {conductivity} ppm "
                f"({simulator.conductivity_source}) and clarity index {clarity} ({clarity_source}) "
                f"both elevated"
            ]

        insert_reading(clarity, conductivity, diverter_active)

        # log only when the diverter changes state, one entry per episode
        if diverter_active and not diverter_was_active:
            active_since = time.time()
            insert_event("DIVERTER_ACTIVATED", ". ".join(reasons))
        elif not diverter_active and diverter_was_active:
            duration = int(time.time() - active_since) if active_since else 0
            insert_event("DIVERTER_CLEARED", f"readings back below thresholds after {duration} s")
            active_since = None
        diverter_was_active = diverter_active

        from_camera = clarity_source == "camera"
        payload = {
            "clarity": clarity,
            "clarity_source": clarity_source,                      # "camera" or "simulated"
            "turbidity_class": cam["turbidity_class"] if from_camera else clarity_class(clarity),
            "brightness": cam.get("brightness") if from_camera else None,
            "debris_count": cam.get("debris_count") if from_camera else None,
            "conductivity": conductivity,
            "conductivity_source": simulator.conductivity_source,  # "sensor" or "simulated"
            "diverter_active": diverter_active,
            "pollution_score": score_level,
            "pollution_value": score_value,
            "causes": reasons if diverter_active else [],
            "timestamp": int(time.time())
        }

        state.latest = payload
        await manager.broadcast(payload)
        await asyncio.sleep(2)


@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    # accept connection and keep alive until client disconnects
    await manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        manager.disconnect(websocket)