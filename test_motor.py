import RPi.GPIO as GPIO
import time


GPIO.setmode(GPIO.BOARD)

GPIO.setup(32, GPIO.OUT)
GPIO.setup(36, GPIO.OUT)

for i in range(5):
    GPIO.output(32, False)
    GPIO.output(36, i%2)
    time.sleep(1)

GPIO.cleanup()