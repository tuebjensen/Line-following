from math import cos, sin, pi
import RPi.GPIO as GPIO
import asyncio
import signal
import sys
from lib_car import Car
from lib_motor import Motor

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

GPIO.setmode(GPIO.BOARD)
car = Car(
    motor_left=Motor(speed_pin=33, direction_pin=31, encoder_interrupt_wiring_pi_pin=25),
    motor_right=Motor(speed_pin=32, direction_pin=36, encoder_interrupt_wiring_pi_pin=0),
    speed=20
)
async def main():
    for i in range(12):
        direction = cos(i * pi / 6), sin(i * pi / 6)
        print(direction)
        car.set_velocity(direction)
        await asyncio.sleep(3)
    # for i in range(3):
    #     direction = (0.05, 0.9)#cos(2 * pi / 50 * i), sin(2 * pi / 50 * i)
    #     car.set_velocity(direction)
    #     await asyncio.sleep(3)
    #     direction = (-0.15, 0.9)#cos(2 * pi / 50 * i), sin(2 * pi / 50 * i)
    #     car.set_velocity(direction)
    #     await asyncio.sleep(3)
    #     direction = (-0.05, -0.9)#cos(2 * pi / 50 * i), sin(2 * pi / 50 * i)
    #     car.set_velocity(direction)
    #     await asyncio.sleep(3)

async def start():
    await asyncio.gather(
        main(), 
        car.start_running(),
    )

asyncio.run(start())