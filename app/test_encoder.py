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
GPIO.setup(32, GPIO.OUT)
GPIO.setup(36, GPIO.OUT)
GPIO.setup(11, GPIO.IN)
pwm = GPIO.PWM(32, 50)
GPIO.add_event_detect(11, GPIO.FALLING, callback=encoder_callback)
GPIO.output(36, False)
pwm.start(5)
while count < 960:
    pass
pwm.ChangeDutyCycle(0)
signal.pause()