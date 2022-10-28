from math import cos, sin, pi
import RPi.GPIO as GPIO
from car import Car
import asyncio

car = Car(32, 36, 33, 31)

async def main():
    GPIO.setmode(GPIO.BOARD)
    for i in range(50):
        direction = (cos(2 * pi / 50 * i), sin(2 * pi / 50 * i))
        car.set_velocity(direction)
        await asyncio.sleep(0.1)
    GPIO.cleanup()

async def run():
    await asyncio.gather(car.start_running(), main())

asyncio.run(run())