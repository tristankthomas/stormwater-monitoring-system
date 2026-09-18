import asyncio
import json
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from database import insert_reading, insert_event
from simulator import simulator, compute_pollution_score, thresholds

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


async def sensor_loop():
    # runs continuously in background, reading sensors and broadcasting every 2 seconds
    while True:
        turbidity, conductivity = simulator.read()
        diverter_active = (
            turbidity > thresholds["turbidity"] or
            conductivity > thresholds["conductivity"]
        )

        insert_reading(turbidity, conductivity, diverter_active)

        if diverter_active:
            msg = f"threshold exceeded — turbidity: {turbidity} NTU, conductivity: {conductivity} ppm"
            insert_event("DIVERTER_TRIGGERED", msg)

        payload = {
            "turbidity": turbidity,
            "conductivity": conductivity,
            "diverter_active": diverter_active,
            "pollution_score": compute_pollution_score(turbidity, conductivity),
            "rain_event": simulator.rain_event,
            "timestamp": int(time.time())
        }

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