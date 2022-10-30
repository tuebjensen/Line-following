import RPi.GPIO as GPIO
from motor import Motor
import asyncio
import signal
import time
import sys
from simple_pid import PID

pid = PID(0.6, 5, 1, setpoint=5000)
pid.sample_time = 0.1
pid.output_limits = (0, 100)
pid.auto_mode = True
interrupt_count = 0
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
    global interrupt_count
    interrupt_count += 1

setup()
motor_pwm = GPIO.PWM(32, 50)
motor_pwm.start(50)

signal.signal(signal.SIGINT, signal_handler)
while True:
    output = pid(interrupt_count)
    interrupt_count = 0
    motor_pwm.ChangeDutyCycle(output)
    print(output)
    time.sleep(0.1)
signal.pause()


