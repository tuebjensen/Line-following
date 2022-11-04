from flask import Flask, render_template, Response

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
from test_line_following import *

app = Flask(__name__)

cap = cv.VideoCapture(0)
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

@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(get_frames_for_server(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)