import asyncio
from math import asin, atan2, cos, pi, sin, sqrt
import time
from typing import Tuple
import cv2 as cv
import numpy as np
import signal
import sys
import RPi.GPIO as GPIO
from lib_calculate_direction import get_direction_vector_of_line, get_displacement_vector_from_center, get_direction_to_go
from lib_car import Car
from lib_motor import Motor
from lib_process_lines import Line, get_centers_of_parallel_line_pairs, get_from_houghlines, merge_lines

cap = None
car = None

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
GPIO.setmode(GPIO.BOARD)

def nothing(x):
    pass

def process_frame(frame, blur, block_size, c):
    processed_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    processed_frame = cv.medianBlur(processed_frame, 2*blur+1)
    processed_frame = cv.adaptiveThreshold(processed_frame, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 2*(block_size+1)+1, c)
    return processed_frame

def find_edges_and_lines(frame):
    edges = cv.Canny(frame, 50, 150, apertureSize = 3)
    lines = cv.HoughLines(edges, 1, np.pi/180, 100)
    return edges, lines

def put_line_on_frame(frame, line: Line, color: Tuple[int, int, int]):
    rho, theta = line.rho, line.theta
    a = np.cos(theta)
    b = np.sin(theta)
    x0 = a*rho
    y0 = b*rho
    x1 = int(x0 + 1000*(-b))
    y1 = int(y0 + 1000*(a))
    x2 = int(x0 - 1000*(-b))
    y2 = int(y0 - 1000*(a))
    cv.line(frame, (x1,y1), (x2,y2), color, 2)

def display_all_lines(lines: 'list[Line]', frame):
    for line in lines:
        color = (255, 0, 0) # blue (BGR)
        put_line_on_frame(frame, line, color)

def display_merged_parallel_lines(merged_lines: 'list[Line]', frame):
    for i in range(len(merged_lines)):
        line = merged_lines[i]
        color = (0, 255-255/len(merged_lines)*i ,0) # shade of green
        put_line_on_frame(frame, line, color)

def display_center_of_parallel_lines(parallel_line_centers, frame):
    if parallel_line_centers is None:
        return
    for i in range(len(parallel_line_centers)):
        line = parallel_line_centers[i]
        color = (0, 0, 255-255/len(parallel_line_centers)*i) # shade of red
        put_line_on_frame(frame, line, color)


def display_displacement_and_direction_vectors(parallel_line_centers, frame):
    if(not isinstance(parallel_line_centers, (list, tuple, np.ndarray))):
        return
    if(len(parallel_line_centers) < 1):
        return
    line = parallel_line_centers[0]
    displacement_vector = get_displacement_vector_from_center(line, frame)
    frame_width = frame.shape[1]
    frame_height = frame.shape[0]
    center_x = frame_width / 2
    center_y = frame_height / 2
    cv.line(frame, (int(center_x), int(center_y)), (int(displacement_vector.x) + int(center_x), int(center_y) - int(displacement_vector.y)), (255,255,0), 2)
    direction_vector = get_direction_vector_of_line(line) * 200
    cv.line(frame,
        (int(displacement_vector.x) + int(center_x), int(center_y) - int(displacement_vector.y)),
        (int(displacement_vector.x) + int(direction_vector.x) + int(center_x), int(center_y) - int(direction_vector.y) - int(displacement_vector.y)),
        (0,255,255),
        2
    )

def display_direction_to_go(parallel_line_centers, frame):
    if(not isinstance(parallel_line_centers, (list, tuple, np.ndarray))):
        return
    if(len(parallel_line_centers) < 1):
        return
    line = parallel_line_centers[0]
    frame_width = frame.shape[1]
    frame_height = frame.shape[0]
    center_x = frame_width / 2
    center_y = frame_height / 2
    direction_to_go = get_direction_to_go(line, frame) * 50
    cv.line(frame, (int(center_x), int(center_y)), (int(direction_to_go.x) + int(center_x), int(center_y) - int(direction_to_go.y)), (0,69,255), 2)

def get_frames_for_server():
    guard = True

    while cap.isOpened() and guard:
        ret, original_frame = cap.read()
        original_frame = original_frame[:, 30:]
        if not ret:
            print("Can't receive next frame")
            cap.set(cv.CAP_PROP_POS_FRAMES, 0)
            continue
        
        blur = 3
        block_size = 5
        c = 3
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
        
        ret, buffer = cv.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
    cap.release()

async def process_video():
    guard = True
    img = np.zeros((25, 500, 3), np.uint8)
    #cv.namedWindow('image')
    #cv.createTrackbar('Blur', 'image', 5, 100, nothing)
    #cv.createTrackbar('Block size', 'image', 5, 100, nothing)
    #cv.createTrackbar('C', 'image', 5, 100, nothing)
    while cap.isOpened() and guard:
        await asyncio.sleep(0.1)

        print('start', time.time())
        ret, original_frame = cap.read()
        original_frame = original_frame[:, 30:]
        #original_frame = cv.flip(original_frame, 1)
        #original_frame = cv.rotate(original_frame, cv.ROTATE_90_CLOCKWISE)
        print(1, time.time())
        if not ret:
            print("Can't receive next frame")
            cap.set(cv.CAP_PROP_POS_FRAMES, 0)
            continue
        
        print(2, time.time())
        blur = 3#cv.getTrackbarPos('Blur', 'image')
        block_size = 5#cv.getTrackbarPos('Block size', 'image')
        c = 3#cv.getTrackbarPos('C', 'image')
        processed_frame = process_frame(original_frame, blur, block_size, c)
        print(3, time.time())
        edges, houghlines = find_edges_and_lines(processed_frame)
        print(4, time.time())

        if isinstance(houghlines, np.ndarray):
            #cv.putText(original_frame, f'lines: {len(houghlines)}', (0,50), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv.LINE_AA)

            print(5, time.time())
            lines = get_from_houghlines(houghlines)
            print(6, time.time())
            merged_lines = merge_lines(lines)
            print(7, time.time())
            parallel_line_centers = get_centers_of_parallel_line_pairs(merged_lines)
            print(8, time.time())
            #display_all_lines(lines, original_frame)
            #display_merged_parallel_lines(merged_lines, original_frame)
            #display_center_of_parallel_lines(parallel_line_centers, original_frame)
            #display_displacement_and_direction_vectors(parallel_line_centers, original_frame)
            #display_direction_to_go(parallel_line_centers, original_frame)
            
            print(9, time.time())
            if parallel_line_centers is not None and len(parallel_line_centers) > 0:
                velocity_vector = get_direction_to_go(parallel_line_centers[0], original_frame)
                direction = velocity_vector.x, velocity_vector.y
                print(str(direction))
                car.set_velocity(direction)

        #cv.imshow('original video', original_frame)
        #cv.imshow('processed video', processed_frame)
        #cv.imshow('edges', edges)
        #cv.imshow('image', img)
        #cv.moveWindow('processed video', 700, 208)
        #cv.moveWindow('edges', 1200, 208)
        #if cv.waitKey(10) == ord('q'):
            #guard = False
    cap.release()
    #cv.destroyAllWindows()

async def start():
    await asyncio.gather(
        car.start_running(),
        process_video()
    )

if __name__ == "__main__":
    cap = cv.VideoCapture(0)
    car = Car(
        motor_left=Motor(speed_pin=33, direction_pin=31, encoder_interrupt_pin=37),
        motor_right=Motor(speed_pin=32, direction_pin=36, encoder_interrupt_pin=11),
        speed=20
    )
    asyncio.run(start())

