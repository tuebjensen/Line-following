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
from lib_calculate_direction import get_direction_vector_of_line, get_displacement_vector_from_center, get_direction_to_go
from lib_car import Car
from lib_motor import Motor
from lib_process_lines import Line, get_centers_of_parallel_line_pairs, get_from_houghlines, merge_lines
from lib_line_following import process_frame, find_edges_and_lines, display_all_lines, display_center_of_parallel_lines, display_direction_to_go, display_displacement_and_direction_vectors, display_merged_parallel_lines
from lib_video_streaming import VideoStreaming

cap = None
car = None
video = VideoStreaming()

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

def process_original_frame(original_frame):
    original_frame = original_frame[:, 30:]
    #original_frame = cv.flip(original_frame, 1)
    #original_frame = cv.rotate(original_frame, cv.ROTATE_90_CLOCKWISE)
    direction = None
    blur = 3#cv.getTrackbarPos('Blur', 'image')
    block_size = 5#cv.getTrackbarPos('Block size', 'image')
    c = 3#cv.getTrackbarPos('C', 'image')
    processed_frame = process_frame(original_frame, blur, block_size, c)
    edges, houghlines = find_edges_and_lines(processed_frame)
    if isinstance(houghlines, np.ndarray):
        lines = get_from_houghlines(houghlines)
        merged_lines = merge_lines(lines)
        parallel_line_centers = get_centers_of_parallel_line_pairs(merged_lines)
        display_all_lines(lines, original_frame)
        display_merged_parallel_lines(merged_lines, original_frame)
        display_center_of_parallel_lines(parallel_line_centers, original_frame)
        display_displacement_and_direction_vectors(parallel_line_centers, original_frame)
        display_direction_to_go(parallel_line_centers, original_frame)
        
        if parallel_line_centers is not None and len(parallel_line_centers) > 0:
            velocity_vector = get_direction_to_go(parallel_line_centers[0], original_frame)
            direction = velocity_vector.y, velocity_vector.x
            #print(str(direction))
    
    ret_encode, buffer = cv.imencode('.jpg', original_frame)
    frame_encoded = buffer.tobytes()
    return frame_encoded, direction

async def process_video():
    with ProcessPoolExecutor() as executor:
        loop = asyncio.get_running_loop()
        #executor = ProcessPoolExecutor()
        while cap.isOpened():
            ret_read, original_frame = cap.read() # <3ms
            if ret_read:
                frame_encoded, direction = await loop.run_in_executor(executor, partial(process_original_frame, original_frame))
                start = perf_counter()
                video.set_frame_encoded(frame_encoded)
                car.set_velocity(direction)
                stop = perf_counter()
                print(stop - start)
            else:
                cap.set(cv.CAP_PROP_POS_FRAMES, 0)
        cap.release()

async def start():
    await asyncio.gather(
        car.start_running(),
        video.start_running('0.0.0.0', 5000),
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
    asyncio.run(start())


