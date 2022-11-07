from lib_motor import Motor
import asyncio
import sys
import RPi.GPIO as GPIO
from time import time
encoder_interrupt_pin = int(sys.argv[1])#[int(e) for e in sys.argv[1:2]]
count = 0
GPIO.setmode(GPIO.BOARD)
GPIO.setup(encoder_interrupt_pin, GPIO.IN)
start = time()
while True:
    now = time()
    timeout = int(100 - (now - start))
    
    if timeout <= 0:
        print(str(count))
        start = now
        continue

    ret_wait = GPIO.wait_for_edge(encoder_interrupt_pin, GPIO.FALLING, timeout = timeout)
    
    if ret_wait is not None:
        count += 1
    else:
        print(str(count))
        start = now