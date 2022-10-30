import RPi.GPIO as GPIO
from motor import Motor
import asyncio
import signal
import time
import sys

curr_time = time.time()

def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(32, GPIO.OUT)
    GPIO.setup(36, GPIO.OUT)
    GPIO.setup(33, GPIO.OUT)
    GPIO.setup(31, GPIO.OUT)
    GPIO.setup(11, GPIO.IN)
    GPIO.add_event_detect(11, GPIO.FALLING, callback=interrupt)

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

def interrupt(channel):
    global curr_time
    print(time.time() - curr_time)
    curr_time = time.time()

setup()
motor_pwm = GPIO.PWM(32, 50)
motor_pwm.start(0)

signal.signal(signal.SIGINT, signal_handler)
for i in range(101):
    motor_pwm.ChangeDutyCycle(i)
    time.sleep(0.1)

signal.pause()


