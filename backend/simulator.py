import random

from conductivity import conductivity_sensor

# shared mutable thresholds — updated at runtime via the settings endpoint
thresholds = {
    "clarity": 1.0,         # camera clarity index at which water counts as turbid (1.0 = the "high" class boundary)
    "conductivity": 800.0   # ppm - elevated conductivity indicates contamination
}


def compute_pollution_score(clarity: float, conductivity: float) -> tuple[float, str]:
    # each signal is scaled so 1.0 means "at its own threshold"
    c = conductivity / thresholds["conductivity"]
    k = clarity / thresholds["clarity"]
    # the worse signal sets the level, the other adds half its weight:
    #   either signal alone at its threshold         -> 1.0 (high)
    #   both moderately elevated (e.g. 0.7 and 0.7)  -> 1.05 (high), combined evidence escalates
    value = max(c, k) + 0.5 * min(c, k)
    if value < 0.5:
        level = "low"
    elif value < 1.0:
        level = "medium"
    else:
        level = "high"
    return round(value, 2), level


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