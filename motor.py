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

        GPIO.setup(speed_pin, GPIO.OUT)
        GPIO.setup(direction_pin, GPIO.OUT)

        # set direction to forward
        GPIO.output(direction_pin, True)
    
    def set_duty(self, duty: str):
        self._duty = duty

    def set_direction(self, is_forward: bool):
        GPIO.output(self.direction_pin, is_forward)

    async def start_running(self):
        # run motors until GPIO is cleaned up
        try:
            while True:
                GPIO.output(self._speed_pin, False)
                await asyncio.sleep(0.02 * self._duty)
                GPIO.output(self._speed_pin, True)
                await asyncio.sleep(0.02 * (1 - self._duty))
        except (RuntimeError):
            pass
