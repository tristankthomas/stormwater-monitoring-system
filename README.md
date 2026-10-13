# Stormwater Monitoring System

A real-time stormwater pollution monitoring prototype. It monitors water quality at a stormwater drain outlet during first-flush rain events, combines a conductivity reading with a camera-derived clarity index into a pollution score, and activates a diverter when that score reaches HIGH. The aim is to limit the first flush of pollutants entering the Yarra.

## Architecture

```
backend/    FastAPI server: sensor reading, camera analysis, SQLite storage, WebSocket broadcasting
frontend/   Vue 3 + Vuetify dashboard: live readings, history chart, event log, settings, live camera feed
```

## Stack

- **Backend:** Python, FastAPI, SQLite, Uvicorn, OpenCV, smbus2
- **Frontend:** Vue 3, Vuetify, ApexCharts, Axios
- **Hardware:** Raspberry Pi 4, CSI camera module (Picamera2), analog conductivity (TDS) probe read through an ADS1115 ADC. A GPIO LED to represent the diverter is planned.

## How it works

### Sensors

- **Conductivity (primary signal).** The probe output is read by an ADS1115 on I2C bus 1 (address 0x48, ADDR tied to GND). The reading is a trimmed mean of 20 samples, converted to mg/L. Each probe needs its own calibration: add voltage and concentration pairs to `CALIBRATION_POINTS` in `backend/conductivity.py`. With fewer than two points a generic TDS curve is used.
- **Water clarity (secondary signal).** The camera frame is converted to greyscale and its mean brightness is mapped to a clarity index between 0 and 2. A value of 0 is clear, and 1 is the boundary for high turbidity. The index measures darkness, so it is sensitive to lighting changes. A debris count is also shown, using adaptive thresholding and contour detection. It is a rough indicator only and does not affect the diverter.
- **Fallback.** If the conductivity sensor or the camera is not available (for example when running on a laptop), simulated values are used. The dashboard shows a LIVE or SIMULATED badge on each reading so the source is always clear.

### Pollution score and diverter

Each signal is scaled so that 1.0 means "at its own threshold":

```
c = conductivity / conductivity_threshold
k = clarity_index / clarity_threshold
score = max(c, k) + 0.5 * min(c, k)
```

The score is LOW below 0.5, MEDIUM below 1.0, and HIGH from 1.0. The diverter is active whenever the score is HIGH. Either signal alone at its threshold gives HIGH, and two moderately elevated signals can combine to reach HIGH. The weighting is a first design and has not yet been tuned against real events.

### Event log

The event log records diverter state changes only. `DIVERTER_ACTIVATED` entries state the cause, including the reading source, and `DIVERTER_CLEARED` entries state how long the diverter was active. A cause that appears after the diverter is already active is not logged separately.

### Settings

- Conductivity threshold (mg/L).
- Camera thresholds: clear brightness, high turbidity brightness and debris minimum area, with a live brightness readout to set them against the real scene.

Thresholds are held in memory and reset when the backend restarts.

## Getting started

### Prerequisites

- Python 3.10+
- Node.js 18+

### Backend

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / Pi
pip install -r backend/requirements.txt
make backend
```

On a laptop the camera and conductivity sensor are not found and simulated data is used.

### Frontend

```bash
cd frontend && npm install
make frontend
```

Open `http://localhost:5173` in your browser. The Vite dev server proxies `/api` and `/ws` to the backend, so the same relative URLs work in development and on the Pi.

## Raspberry Pi

1. Enable I2C (`sudo raspi-config`, Interface Options) and connect the ADS1115 to I2C bus 1 (pins 3 and 5). `i2cdetect -y 1` should show `48`.
2. Install dependencies from `requirements-pi.txt`. This includes `smbus2` and `opencv-python-headless`, because the Lite OS has no libGL.
3. Copy the backend with `deploy.bat`, then run `make run-pi` on the Pi.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | Latest snapshot from the sensor loop |
| GET | `/api/readings` | Historical readings from SQLite |
| GET | `/api/events` | Diverter event log |
| GET / POST | `/api/thresholds` | Read or set the conductivity threshold (`?conductivity=`) |
| POST | `/api/thresholds/reset` | Reset the conductivity threshold |
| GET | `/api/camera/analysis` | Latest camera analysis |
| GET | `/api/camera/stream` | MJPEG live feed |
| GET / POST | `/api/camera/thresholds` | Read or set the camera thresholds |
| POST | `/api/camera/thresholds/reset` | Reset the camera thresholds |
| DELETE | `/api/clear` | Clear readings and events |
| WS | `/ws/live` | Live sensor stream at 2 s intervals |

## Production

Build the frontend and serve static files via FastAPI:

```bash
cd frontend && npm run build
# copy dist/ to backend/static/
make backend
```

Then open `http://<device-ip>:8000` from any device on the same network.

## Known limitations

- Conductivity calibration is pending, so readings are indicative until `CALIBRATION_POINTS` is filled in.
- The clarity index depends on lighting and is not a turbidity measurement.
- Debris detection is not validated.
- Thresholds are not persisted across restarts.