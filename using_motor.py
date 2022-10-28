from math import cos, sin, pi
import RPi.GPIO as GPIO
from car import Car
import asyncio

GPIO.setmode(GPIO.BOARD)
car = Car(32, 36, 33, 31)

async def main():
    for i in range(3):
        direction = (i / 2 - 0.5, -0.9)
        car.set_velocity(direction)
        await asyncio.sleep(0.1)
    GPIO.cleanup()

async def run():
    await asyncio.gather(car.start_running(), main())

asyncio.run(run())