from time import time
import RPi.GPIO as GPIO
import sys
import signal
count = 0

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def encoder_callback(arg):
    global count
    count += 1
    print(count)

GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN)
GPIO.add_event_detect(11, GPIO.FALLING, callback=encoder_callback)

signal.pause()