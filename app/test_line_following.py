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
from lib_line_following import get_processed_frame_and_direction_vector
from lib_car import Car
from lib_motor import Motor
from lib_web_server import WebServer

cap = None
car = None
video = WebServer()
image_processor = None
line_processor = None
direction_calculator = None


def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

def nothing():
    pass

path_plan = []
unread_new_path = False

def write_path(path):
    global path_plan
    path_plan = path[1:]
    global unread_new_path
    unread_new_path = True

def read_path():
    global unread_new_path
    unread_new_path = False
    global path_plan
    return path_plan


async def process_video():
    global direction_calculator_state
    with ProcessPoolExecutor() as executor:
        loop = asyncio.get_running_loop()
        #executor = ProcessPoolExecutor()
        while cap.isOpened():
            ret_read, original_frame = cap.read() # <3ms
            if ret_read:
                #print(f'Before: {direction_calculator}')
                if(unread_new_path):
                    path = read_path()
                    direction_calculator.set_new_path(path)
                processed_frame_info = await loop.run_in_executor(executor,
                    partial(get_processed_frame_and_direction_vector,
                        original_frame,
                        image_processor,
                        line_processor,
                        direction_calculator))
                frame = processed_frame_info['frame']
                velocity_vector = processed_frame_info['velocity_vector']
                current_node = processed_frame_info['current_node']
                direction_calculator.copy(processed_frame_info['direction_calculator'])
                #print(f'After:  {direction_calculator}')
                #print('\n\n')
                ret, buffer = cv.imencode('.jpg', frame)
                frame_encoded = buffer.tobytes()
                video.set_frame_encoded(frame_encoded)
                await video.set_current_node(current_node)
                car.set_velocity(velocity_vector)
            else:
                cap.set(cv.CAP_PROP_POS_FRAMES, 0)
        cap.release()

async def start():
    await asyncio.gather(
        car.start_running(),
        video.start_running('0.0.0.0', 5000, write_path),
        process_video()
    )

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    GPIO.setmode(GPIO.BOARD)

    cap = cv.VideoCapture(0)
    car = Car(
        motor_left=Motor(speed_pin=33, direction_pin=31, encoder_interrupt_wiring_pi_pin=25),
        motor_right=Motor(speed_pin=32, direction_pin=36, encoder_interrupt_wiring_pi_pin=0),
        speed=25
    )
    image_processor = ImageProcessor(10, 5, 7, 65)
    line_processor = LineProcessor()
    direction_calculator = DirectionCalculator(state_change_threshold=5, react_to_intersection_threshold=0.0)
    asyncio.run(start())


