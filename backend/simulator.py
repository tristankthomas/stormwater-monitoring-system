import random

# pollution thresholds based on water quality standards
TURBIDITY_THRESHOLD = 50.0      # NTU - above this triggers diverter
CONDUCTIVITY_THRESHOLD = 800.0  # ppm - elevated conductivity indicates contamination


def compute_pollution_score(turbidity: float, conductivity: float) -> str:
    # turbidity weighted higher as the primary visual indicator
    score = (turbidity / TURBIDITY_THRESHOLD) * 0.6 + (conductivity / CONDUCTIVITY_THRESHOLD) * 0.4
    if score < 0.5:
        return "low"
    elif score < 1.0:
        return "medium"
    else:
        return "high"


class SensorSimulator:
    # simulates realistic sensor behaviour including first-flush rain events
    def __init__(self):
        self.rain_event = False
        self.rain_timer = 0

    def read(self) -> tuple[float, float]:
        # randomly trigger a rain event with low probability each cycle
        if not self.rain_event and random.random() < 0.005:
            self.rain_event = True
            self.rain_timer = random.randint(20, 60)  # event lasts 40-120 seconds at 2s intervals

        if self.rain_event:
            # first-flush: elevated turbidity and conductivity from road runoff
            turbidity = random.uniform(60, 120)
            conductivity = random.uniform(900, 1500)
            self.rain_timer -= 1
            if self.rain_timer <= 0:
                self.rain_event = False
        else:
            # baseline dry weather readings
            turbidity = random.uniform(5, 30)
            conductivity = random.uniform(200, 600)

        return round(turbidity, 2), round(conductivity, 2)


# single shared simulator instance used across the app
simulator = SensorSimulator()
