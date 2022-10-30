import RPi.GPIO as GPIO
from motor import Motor
import asyncio

GPIO.setmode(GPIO.BOARD)
motor = Motor(32, 36)

GPIO.setup(33, GPIO.OUT)
GPIO.setup(31, GPIO.OUT)

for i in range(5):
    GPIO.output(32, False)
    GPIO.output(36, 1 if i%2 == 0 else -1)
    time.sleep(1)

GPIO.cleanup()
