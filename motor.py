import RPi.GPIO as GPIO
import asyncio

class Motor:
    def __init__(
        self,
        speed_pin: int,
        direction_pin: int,
        default_duty: float = 0
    ):
        self._speed_pin = speed_pin
        self._direction_pin = direction_pin
        self._duty = default_duty
        self._direction = False

        GPIO.setup(speed_pin, GPIO.OUT)
        GPIO.setup(direction_pin, GPIO.OUT)

    def set_velocity(self, velocity: float):
        if velocity > 0:
            self._duty = 1 - velocity
            self._direction = False
        else:
            self._duty = 1 + velocity
            self._direction = True

    async def start_running(self):
        # run motors until GPIO is cleaned up
        try:
            while True:
                GPIO.output(self._direction_pin, self._direction)
                GPIO.output(self._speed_pin, True)
                await asyncio.sleep(0.02 * self._duty)
                GPIO.output(self._speed_pin, False)
                await asyncio.sleep(0.02 * (1 - self._duty))
        except (RuntimeError):
            pass
