try:
    from gpiozero import LED
except Exception:
    LED = None

# BCM pin number, GPIO17 is physical pin 11. Wire: pin -> resistor (220 to 330 ohm) -> LED anode, LED cathode -> GND
LED_PIN = 17


class DiverterLED:
    # mirrors the diverter state on a physical LED, does nothing when GPIO is not available
    def __init__(self):
        self.available = False
        self._led = None
        if LED is None:
            return
        try:
            self._led = LED(LED_PIN)
            self.available = True
        except Exception as e:
            print(f"diverter LED not available: {e}")

    def set(self, active: bool):
        if not self.available:
            return
        if active:
            self._led.on()
        else:
            self._led.off()


diverter_led = DiverterLED()
