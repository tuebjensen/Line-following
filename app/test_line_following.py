import asyncio
from functools import partial
from concurrent.futures import ProcessPoolExecutor
from math import asin, atan2, cos, pi, sin, sqrt
from typing import Tuple
from time import perf_counter
import cv2 as cv
import numpy as np
import signal
import sys
import RPi.GPIO as GPIO
from lib_calculate_direction import DirectionCalculator
from lib_image_processing import ImageProcessor
from lib_process_lines import LineProcessor
from test_line_processing import get_processed_frame
from lib_car import Car
from lib_motor import Motor
from lib_web_server import WebServer
from os import getpid

cap = None
car = None
video = WebServer()
image_processor = None
line_processor = None
direction_calculator = None
direction_calculator_state = {
    'stable_state': 0,
    'last_incoming_state': 1,
    'last_incoming_state_count': 10,
    'path_plan': ['straight', 'straight', 'straight', 'straight']
}


def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

def nothing():
    pass


async def process_video():
    global direction_calculator_state
    with ProcessPoolExecutor() as executor:
        loop = asyncio.get_running_loop()
        #executor = ProcessPoolExecutor()
        while cap.isOpened():
            ret_read, original_frame = cap.read() # <3ms
            if ret_read:
                print(f'Before: {direction_calculator}')
                print(f'Before: {direction_calculator_state}')
                frame, direction, current_node, next_direction_calculator_state = await loop.run_in_executor(executor,
                    partial(get_processed_frame,
                        original_frame,
                        image_processor,
                        line_processor,
                        direction_calculator,
                        direction_calculator_state))
                direction_calculator_state = next_direction_calculator_state
                # await video.set_current_node(current_node)
                ret, buffer = cv.imencode('.jpg', frame)
                frame_encoded = buffer.tobytes()
                video.set_frame_encoded(frame_encoded)
                car.set_velocity(direction)
                print(f'After:  {direction_calculator_state}')
                print(f'After:  {direction_calculator}')
                print('\n\n')
            else:
                cap.set(cv.CAP_PROP_POS_FRAMES, 0)
        cap.release()

async def start():
    await asyncio.gather(
        car.start_running(),
        video.start_running('0.0.0.0', 5000, direction_calculator.set_new_path),
        process_video()
    )

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    GPIO.setmode(GPIO.BOARD)

    cap = cv.VideoCapture(0)
    car = Car(
        motor_left=Motor(speed_pin=33, direction_pin=31, encoder_interrupt_wiring_pi_pin=25),
        motor_right=Motor(speed_pin=32, direction_pin=36, encoder_interrupt_wiring_pi_pin=0),
        speed=20
    )
    image_processor = ImageProcessor(10, 5, 7, 85)
    line_processor = LineProcessor()
    direction_calculator = DirectionCalculator()
    asyncio.run(start())


