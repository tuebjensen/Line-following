import RPi.GPIO as GPIO
from motor import Motor
import asyncio

GPIO.setmode(GPIO.BOARD)
motor = Motor(32, 36)

async def main():
    GPIO.setmode(GPIO.BOARD)
    for f in range(-1, 1, 0.1):
        motor.set_velocity(f)
        await asyncio.sleep(0.5)
    GPIO.cleanup()

async def run():
    await asyncio.gather(car.start_running(), main())

asyncio.run(run())