from lib_motor import Motor
import asyncio
import sys
import RPi.GPIO as GPIO

encoder_interrupt_pin = sys.argv[1]#[int(e) for e in sys.argv[1:2]]

GPIO.setmode(GPIO.BOARD)
GPIO.setup(encoder_interrupt_pin, GPIO.IN)
GPIO.wait_for_edge(encoder_interrupt_pin, GPIO.FALLING, timeout = 100)
