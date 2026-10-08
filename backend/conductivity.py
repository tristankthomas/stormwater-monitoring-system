import threading
import time

# smbus2 only works on linux (the pi), import conditionally like picamera2
try:
    from smbus2 import SMBus
    SMBUS_AVAILABLE = True
except ImportError:
    SMBUS_AVAILABLE = False

ADS_ADDR = 0x48
REG_CONVERSION = 0x00
REG_CONFIG = 0x01
FULL_SCALE_V = 4.096  # PGA setting in the config word below (+/-4.096 V)
TEMP_C = 25.0         # no temperature sensor yet, assume 25 C

# (voltage, ppm) pairs measured against known salt solutions.
# leave empty to use the generic curve; with 2+ points the readings are
# interpolated linearly between them (and extrapolated past the ends)
CALIBRATION_POINTS: list[tuple[float, float]] = []


def _generic_curve(v: float) -> float:
    # standard Gravity-style TDS curve (rated 0-1000 ppm), with temperature compensation
    comp = 1.0 + 0.02 * (TEMP_C - 25.0)
    vc = v / comp
    return (133.42 * vc ** 3 - 255.86 * vc ** 2 + 857.39 * vc) * 0.5


def _calibrated_curve(v: float) -> float:
    pts = sorted(CALIBRATION_POINTS)
    if v <= pts[0][0]:
        (x0, y0), (x1, y1) = pts[0], pts[1]
    elif v >= pts[-1][0]:
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
    else:
        for i in range(len(pts) - 1):
            if pts[i][0] <= v <= pts[i + 1][0]:
                (x0, y0), (x1, y1) = pts[i], pts[i + 1]
                break
    if x1 == x0:
        return y0
    return y0 + (y1 - y0) * (v - x0) / (x1 - x0)


def voltage_to_ppm(v: float) -> float:
    if len(CALIBRATION_POINTS) >= 2:
        ppm = _calibrated_curve(v)
    else:
        ppm = _generic_curve(v)
    return max(0.0, ppm)


class ConductivitySensor:
    def __init__(self):
        self.bus = None
        self.available = False
        self.lock = threading.Lock()  # keeps i2c transactions from interleaving

        if SMBUS_AVAILABLE:
            self._init_bus()

    def _init_bus(self):
        # try one reading so we know an adc is actually answering at ADS_ADDR
        try:
            self.bus = SMBus(1)
            self._read_voltage()
            self.available = True
        except Exception as e:
            print(f"conductivity sensor not available: {e}")
            self.bus = None
            self.available = False

    def _read_voltage(self) -> float:
        # single-shot, A0 vs GND, +/-4.096 V, 128 SPS, comparator off
        self.bus.write_i2c_block_data(ADS_ADDR, REG_CONFIG, [0xC3, 0x83])
        time.sleep(0.012)
        hi, lo = self.bus.read_i2c_block_data(ADS_ADDR, REG_CONVERSION, 2)
        raw = (hi << 8) | lo
        if raw >= 0x8000:
            raw -= 0x10000
        return raw * FULL_SCALE_V / 32768

    def read_voltage(self, samples: int = 20) -> float:
        # take a burst of samples and average the middle half to reject noise
        with self.lock:
            vals = sorted(self._read_voltage() for _ in range(samples))
        q = samples // 4
        mid = vals[q:samples - q]
        return sum(mid) / len(mid)

    def read_ppm(self) -> float:
        # blocks for about a quarter of a second, so call it from a thread in async code
        return voltage_to_ppm(self.read_voltage())


# single shared sensor instance used across the app
conductivity_sensor = ConductivitySensor()
