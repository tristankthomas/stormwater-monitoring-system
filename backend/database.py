import sqlite3
import time

DB_PATH = "stormwater.db"


def get_conn():
    # open a new connection for each request (sqlite is not thread-safe with shared connections)
    return sqlite3.connect(DB_PATH)


def init_db():
    # create tables on first run if they don't exist
    conn = get_conn()
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
    # store sensor reading with unix timestamp
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO readings (timestamp, turbidity, conductivity, diverter_active) VALUES (?, ?, ?, ?)",
        (int(time.time()), round(turbidity, 2), round(conductivity, 2), int(diverter_active))
    )
    conn.commit()
    conn.close()


def insert_event(event_type: str, message: str):
    # log threshold breaches and diverter activations
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO events (timestamp, event_type, message) VALUES (?, ?, ?)",
        (int(time.time()), event_type, message)
    )
    conn.commit()
    conn.close()


def get_recent_readings(limit: int = 50) -> list[dict]:
    # return most recent readings, reversed so oldest is first for charting
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT timestamp, turbidity, conductivity, diverter_active FROM readings ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    rows = c.fetchall()
    conn.close()
    return [
        {
            "timestamp": r[0],
            "turbidity": r[1],
            "conductivity": r[2],
            "diverter_active": bool(r[3])
        }
        for r in rows
    ]


def get_recent_events(limit: int = 20) -> list[dict]:
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT timestamp, event_type, message FROM events ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    rows = c.fetchall()
    conn.close()
    return [{"timestamp": r[0], "event_type": r[1], "message": r[2]} for r in rows]


def clear_db():
    # delete all readings and events — called before a demo to start fresh
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM readings")
    c.execute("DELETE FROM events")
    conn.commit()
    conn.close()
