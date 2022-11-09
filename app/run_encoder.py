from lib_motor import Motor
import asyncio
import sys
import RPi.GPIO as GPIO
from time import sleep

encoder_interrupt_pin = int(sys.argv[1])#[int(e) for e in sys.argv[1:2]]
count = 0
start = time()
last_val = False

GPIO.setmode(GPIO.BOARD)
GPIO.setup(encoder_interrupt_pin, GPIO.IN)

def callback ():
    count += 1

GPIO.add_event_detect(encoder_interrupt_pin, GPIO.FALLING, callback)

while True:
    now = time()
    sleep(0.1)