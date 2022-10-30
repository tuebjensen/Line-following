from math import cos, sin, pi
import RPi.GPIO as GPIO
from car import Car
import asyncio
import signal
import sys

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

GPIO.setmode(GPIO.BOARD)
car = Car(32, 36, 11, 33, 31, 37)
#motor1 = Motor(speed_pin=32, direction_pin=36, encoder_interrupt_pin=11, speed=20, forwards=False)
#motor2 = Motor(speed_pin=33, direction_pin=31, encoder_interrupt_pin=37, speed=20, forwards=True)
async def main():
    for i in range(50):
        direction = 0.05, 0.9#cos(2 * pi / 50 * i), sin(2 * pi / 50 * i)
        car.set_velocity(direction)
        await asyncio.sleep(0.1)

async def start():
    await asyncio.gather(
        main(), 
        car.start_running()
    )

asyncio.run(start())