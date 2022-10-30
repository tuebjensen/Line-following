import RPi.GPIO as GPIO
from motor import Motor
import asyncio
import signal
import sys

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

GPIO.setmode(GPIO.BOARD)
motor1 = Motor(speed_pin=32, direction_pin=36, encoder_interrupt_pin=11, speed=20, forwards=False)
motor2 = Motor(speed_pin=33, direction_pin=31, encoder_interrupt_pin=37, speed=20, forwards=False)

async def start():
    await asyncio.gather(
        motor1.start_running(),
        motor2.start_running()
    )

asyncio.run(start())