from lib_motor import Motor
import asyncio
import sys
import RPi.GPIO as GPIO
from time import time

encoder_interrupt_pin = int(sys.argv[1])#[int(e) for e in sys.argv[1:2]]
count = 0
start = time()
last_val = False

GPIO.setmode(GPIO.BOARD)
GPIO.setup(encoder_interrupt_pin, GPIO.IN)

while True:
    now = time()
    timeout = int(100 - (now - start) * 1000)
    
    if timeout <= 0:
        sys.stdout.write(str(count) + '\n')
        start = now
        count = 0
        continue

    if GPIO.input(encoder_interrupt_pin) != last_val:
        last_val = not last_val
        count += 1