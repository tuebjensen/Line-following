from lib_process_lines import Line, LineProcessor
from lib_vector2d import Vector2D
import cv2 as cv
import numpy as np

BOX_SIZE = 20


def put_line_on_frame(frame, line: Line, color: 'tuple[int, int, int]'):
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


def display_boxes_around_merged_lines(merged_lines: 'list[Line]', frame, edges):
    line_processor = LineProcessor()
    for i in range(len(merged_lines)):
        line = merged_lines[i]
        color = (0, 255-255/len(merged_lines)*i ,0) # same shade of green as the merged line
        boxes = line_processor._get_box_centers(line, edges)
        for box in boxes:
            x, y = box
            x = int(x)
            y = int(y)
            half_box_size = int(BOX_SIZE/2)
            cv.line(frame, (x - half_box_size, y - half_box_size), (x + half_box_size, y - half_box_size), color, 1)
            cv.line(frame, (x - half_box_size, y - half_box_size), (x - half_box_size, y + half_box_size), color, 1)
            cv.line(frame, (x + half_box_size, y + half_box_size), (x + half_box_size, y - half_box_size), color, 1)
            cv.line(frame, (x + half_box_size, y + half_box_size), (x - half_box_size, y + half_box_size), color, 1)


def display_merged_lines_segments(merged_lines_segments, frame):
    merged_lines = list(merged_lines_segments.keys())
    for i in range(len(merged_lines)):
        line_segments = merged_lines_segments[merged_lines[i]]
        for j in range(len(line_segments)):
            color = (0, (255 - 255/len(merged_lines)*i) / 2, 255-255/len(merged_lines)*i)
            cv.line(frame, (line_segments[j].start_point[0],line_segments[j].start_point[1]), (line_segments[j].end_point[0],line_segments[j].end_point[1]), color, 2)


def display_tape_paths(tape_paths_and_lines, frame):
    if tape_paths_and_lines is None:
        return
    tape_paths = list(tape_paths_and_lines.keys())
    for i in range(len(tape_paths)):
        tape_path = tape_paths[i]
        color = (255-255/len(tape_paths)*i, 0, 255-255/len(tape_paths)*i)
        cv.line(frame, (tape_path.start_point[0], tape_path.start_point[1]), (tape_path.end_point[0], tape_path.end_point[1]), color, 2)


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

def display_displacement_and_direction_vectors(displacement_vector, direction_vector, frame):
    frame_width = frame.shape[1]
    frame_height = frame.shape[0]
    center_x = frame_width / 2
    center_y = frame_height / 2
    cv.line(frame, (int(center_x), int(center_y)), (int(displacement_vector.x) + int(center_x), int(center_y) + int(displacement_vector.y)), (255,255,0), 2)
    cv.line(frame,
        (int(displacement_vector.x) + int(center_x), int(center_y) + int(displacement_vector.y)),
        (int(displacement_vector.x) + int(direction_vector.x) + int(center_x), int(center_y) + int(direction_vector.y) + int(displacement_vector.y)),
        (0,255,255),
        2
    )

def display_direction_to_go(direction_to_go: Vector2D, frame):
    frame_width = frame.shape[1]
    frame_height = frame.shape[0]
    center_x = frame_width / 2
    center_y = frame_height / 2
    direction_to_go = direction_to_go.normalize() * 50
    cv.line(frame, (int(center_x), int(center_y)), (int(direction_to_go.x) + int(center_x), int(center_y) + int(direction_to_go.y)), (0,69,255), 2)
