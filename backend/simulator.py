import random

from conductivity import conductivity_sensor

# shared mutable thresholds — updated at runtime via the settings endpoint
thresholds = {
    "clarity": 1.0,         # camera clarity index at which water counts as turbid (1.0 = the "high" class boundary)
    "conductivity": 800.0   # ppm - elevated conductivity indicates contamination
}


def compute_pollution_score(clarity: float, conductivity: float) -> str:
    # conductivity weighted higher as the primary quantitative signal, camera clarity is the secondary visual check
    score = (conductivity / thresholds["conductivity"]) * 0.6 + (clarity / thresholds["clarity"]) * 0.4
    if score < 0.5:
        return "low"
    elif score < 1.0:
        return "medium"
    else:
        return "high"


class SensorSimulator:
    # stand-in readings used when the real hardware is not attached (e.g. on a laptop)
    def __init__(self):
        self.conductivity_source = "simulated"  # "sensor" or "simulated"

    def simulated_clarity(self) -> float:
        # 0 = clear, 1 = the "high turbidity" boundary; baseline dry weather stays well below it
        return round(max(0.0, random.uniform(-0.3, 0.5)), 3)

    def read_conductivity(self) -> float:
        # baseline dry weather reading, replaced by the real sensor when one is attached
        value = random.uniform(200, 600)
        self.conductivity_source = "simulated"
        if conductivity_sensor.available:
            try:
                value = conductivity_sensor.read_ppm()
                self.conductivity_source = "sensor"
            except Exception as e:
                print(f"conductivity read failed, using simulated value: {e}")
        return round(value, 2)


# single shared simulator instance used across the app
simulator = SensorSimulator()