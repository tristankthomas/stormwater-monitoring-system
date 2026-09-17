from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sqlite3
import asyncio
import random
import json
import time
import os

app = FastAPI()

# allow requests from vue dev server during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "stormwater.db"

# pollution thresholds based on water quality standards
TURBIDITY_THRESHOLD = 50.0      # NTU - above this triggers diverter
CONDUCTIVITY_THRESHOLD = 800.0  # ppm - elevated conductivity indicates contamination


def init_db():
    # create tables if they don't exist on first run
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            turbidity REAL NOT NULL,
            conductivity REAL NOT NULL,
            diverter_active INTEGER NOT NULL DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            message TEXT
        )
    ''')
    conn.commit()
    conn.close()


def insert_reading(turbidity: float, conductivity: float, diverter_active: bool):
    # store each sensor reading with unix timestamp
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO readings (timestamp, turbidity, conductivity, diverter_active) VALUES (?, ?, ?, ?)",
        (int(time.time()), round(turbidity, 2), round(conductivity, 2), int(diverter_active))
    )
    conn.commit()
    conn.close()


def insert_event(event_type: str, message: str):
    # log significant events like threshold breaches and diverter activations
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO events (timestamp, event_type, message) VALUES (?, ?, ?)",
        (int(time.time()), event_type, message)
    )
    conn.commit()
    conn.close()


def get_recent_readings(limit: int = 50):
    # return readings in reverse chronological order for the history chart
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT timestamp, turbidity, conductivity, diverter_active FROM readings ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    rows = c.fetchall()
    conn.close()
    return [{"timestamp": r[0], "turbidity": r[1], "conductivity": r[2], "diverter_active": bool(r[3])} for r in rows]


def get_recent_events(limit: int = 20):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT timestamp, event_type, message FROM events ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    rows = c.fetchall()
    conn.close()
    return [{"timestamp": r[0], "event_type": r[1], "message": r[2]} for r in rows]


def compute_pollution_score(turbidity: float, conductivity: float) -> str:
    # weighted score: turbidity weighted higher as primary visual indicator
    score = (turbidity / TURBIDITY_THRESHOLD) * 0.6 + (conductivity / CONDUCTIVITY_THRESHOLD) * 0.4
    if score < 0.5:
        return "low"
    elif score < 1.0:
        return "medium"
    else:
        return "high"


init_db()


class SensorSimulator:
    # simulates realistic sensor behaviour including first-flush rain events
    def __init__(self):
        self.rain_event = False
        self.rain_timer = 0

    def read(self):
        # randomly trigger a rain event with low probability each cycle
        if not self.rain_event and random.random() < 0.005:
            self.rain_event = True
            self.rain_timer = random.randint(20, 60)  # rain event lasts 40-120 seconds

        if self.rain_event:
            # during rain: elevated turbidity and conductivity simulating first flush
            turbidity = random.uniform(60, 120)
            conductivity = random.uniform(900, 1500)
            self.rain_timer -= 1
            if self.rain_timer <= 0:
                self.rain_event = False
        else:
            # baseline readings during dry conditions
            turbidity = random.uniform(5, 30)
            conductivity = random.uniform(200, 600)

        return round(turbidity, 2), round(conductivity, 2)


simulator = SensorSimulator()


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
        # push data to all connected clients, remove any dead connections
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
        diverter_active = turbidity > TURBIDITY_THRESHOLD or conductivity > CONDUCTIVITY_THRESHOLD

        insert_reading(turbidity, conductivity, diverter_active)

        if diverter_active:
            # log the event when thresholds are exceeded
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


@app.on_event("startup")
async def startup():
    # start the sensor loop as a background task on server startup
    asyncio.create_task(sensor_loop())


@app.get("/api/readings")
def get_readings(limit: int = 50):
    # returns historical readings for the time-series chart
    return get_recent_readings(limit)


@app.get("/api/events")
def get_events(limit: int = 20):
    # returns recent threshold breach events for the event log
    return get_recent_events(limit)


@app.get("/api/status")
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


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    # accept connection and keep alive until client disconnects
    await manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        manager.disconnect(websocket)