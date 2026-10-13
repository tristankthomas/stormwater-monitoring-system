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

# (voltage, mg/L) pairs measured against known salt solutions.
# with 3+ points a quadratic C(V) is least-squares fitted to them at startup,
# with fewer points the generic curve is used. recalibrating only means editing this list
# calibrated on 13 Oct 2026 with the probe in 0, 100, 250, 500, 750 and 1000 mg/L salt solutions
CALIBRATION_POINTS: list[tuple[float, float]] = [
    (0.014, 0.0),
    (0.246, 100.0),
    (0.486, 250.0),
    (0.911, 500.0),
    (1.321, 750.0),
    (1.618, 1000.0),
]


def _generic_curve(v: float) -> float:
    # standard Gravity-style TDS curve (rated 0-1000 ppm), with temperature compensation
    comp = 1.0 + 0.02 * (TEMP_C - 25.0)
    vc = v / comp
    return (133.42 * vc ** 3 - 255.86 * vc ** 2 + 857.39 * vc) * 0.5


def _fit_polynomial(points: list[tuple[float, float]], degree: int) -> list[float]:
    # least-squares polynomial fit of mg/L against voltage, returns coefficients lowest power first.
    # solves the normal equations with gaussian elimination so no numpy is needed on the pi
    n = degree + 1
    a = [[sum(v ** (i + j) for v, _ in points) for j in range(n)] for i in range(n)]
    b = [sum(c * v ** i for v, c in points) for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
        a[col], a[pivot] = a[pivot], a[col]
        b[col], b[pivot] = b[pivot], b[col]
        for r in range(col + 1, n):
            f = a[r][col] / a[col][col]
            for k in range(col, n):
                a[r][k] -= f * a[col][k]
            b[r] -= f * b[col]
    coeffs = [0.0] * n
    for i in range(n - 1, -1, -1):
        coeffs[i] = (b[i] - sum(a[i][j] * coeffs[j] for j in range(i + 1, n))) / a[i][i]
    return coeffs


# quadratic is used because the probe response flattens at high concentration but only six points
# are available, a cubic fits them more tightly but generalises worse (leave-one-out error doubles)
CALIBRATION_DEGREE = 2
_CAL_COEFFS = (
    _fit_polynomial(CALIBRATION_POINTS, CALIBRATION_DEGREE)
    if len(CALIBRATION_POINTS) > CALIBRATION_DEGREE else None
)


def _calibrated_curve(v: float) -> float:
    return sum(c * v ** i for i, c in enumerate(_CAL_COEFFS))


def generic_ppm(v: float) -> float:
    # the uncalibrated reading from the standard TDS curve, shown beside the calibrated mg/L value
    return max(0.0, _generic_curve(v))


def voltage_to_ppm(v: float) -> float:
    if _CAL_COEFFS is not None:
        ppm = _calibrated_curve(v)
    else:
        ppm = _generic_curve(v)
    return max(0.0, ppm)


class ConductivitySensor:
    def __init__(self):
        self.bus = None
        self.available = False
        self.last_voltage = None      # most recent filtered voltage, used to show the uncalibrated reading too
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
        v = self.read_voltage()
        self.last_voltage = v
        return voltage_to_ppm(v)


# single shared sensor instance used across the app
conductivity_sensor = ConductivitySensor()