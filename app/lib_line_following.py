from math import asin, atan2, cos, pi, sin, sqrt
from typing import Tuple
import cv2 as cv
import numpy as np
from lib_calculate_direction import get_direction_vector_of_line, get_displacement_vector_from_center, get_direction_to_go
from lib_process_lines import Line


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

def display_direction_to_go(displacement_vector, direction_vector, frame):
    frame_width = frame.shape[1]
    frame_height = frame.shape[0]
    center_x = frame_width / 2
    center_y = frame_height / 2
    direction_to_go = get_direction_to_go(displacement_vector, direction_vector, frame) * 50
    cv.line(frame, (int(center_x), int(center_y)), (int(direction_to_go.x) + int(center_x), int(center_y) - int(direction_to_go.y)), (0,69,255), 2)

