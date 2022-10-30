import RPi.GPIO as GPIO
import time
import sys
import signal

curr_time = time.time()

def signal_handler(sig, frame):
        GPIO.cleanup()
        sys.exit(0)

def interrupt(channel):
        print(time.time() - curr_time)
        curr_time = time.time()

GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN)

GPIO.add_event_detect(11, GPIO.FALLING, callback=interrupt, bouncetime = 20)

signal.signal(signal.SIGINT, signal_handler)
signal.pause()