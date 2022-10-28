import RPi.GPIO as GPIO
import asyncio

class Motor:
    def __init__(
        self,
        speed_pin: int,
        direction_pin: int,
        default_velocity: float = 0
    ):
        self._speed_pin = speed_pin
        self._direction_pin = direction_pin
        self._velocity = default_velocity

        GPIO.setup(speed_pin, GPIO.OUT)
        GPIO.setup(direction_pin, GPIO.OUT)

    def set_velocity(self, velocity: float):
        self._velocity = velocity

    async def start_running(self):
        # run motors until GPIO is cleaned up
        try:
            while True:
                GPIO.output(self._direction_pin, True if self._velocity > 0 else False)

                GPIO.output(self._speed_pin, self._velocity < 0)
                await asyncio.sleep(0.02 * self._velocity)
                GPIO.output(self._speed_pin, self._velocity > 0)
                await asyncio.sleep(0.02 * (1 - self._velocity))
        except (RuntimeError):
            pass
