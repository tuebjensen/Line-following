import RPi.GPIO as GPIO
import asyncio

motor_direction_pin = 36
motor_speed_pin = 32
motor_duty = 0

async def run_motors():
    # run motors until GPIO is cleaned up
    try:
        while True:
            GPIO.output(motor_speed_pin, False)
            await asyncio.sleep(0.02 * motor_duty)
            GPIO.output(motor_speed_pin, True)
            await asyncio.sleep(0.02 * (1-motor_duty))
    except (RuntimeError):
        pass

async def main():
    global motor_duty

    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(32, GPIO.OUT)
    GPIO.setup(36, GPIO.OUT)

    # set direction to forward
    GPIO.output(motor_direction_pin, True)

    for i in range(10):
        await asyncio.sleep(1)
        motor_duty = motor_duty + 0.1

    GPIO.cleanup()

async def start():
    await asyncio.gather(main(), run_motors())

asyncio.run(start())
