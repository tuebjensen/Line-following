import cv2 as cv
import numpy as np
from typing import Tuple
from lib_process_lines import Line, BOX_SIZE, get_tape_paths, _get_box_centers_please, get_centers_of_parallel_line_pairs, get_from_houghlines, get_tape_corner_line_segments_please, merge_lines
from lib_calculate_direction import get_direction_to_go, get_direction_vector_of_line, get_displacement_vector_from_center



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

def display_boxes_around_merged_lines(merged_lines: 'list[Line]', frame, edges):
    for i in range(len(merged_lines)):
        line = merged_lines[i]
        color = (0, 255-255/len(merged_lines)*i ,0) # same shade of green as the merged line
        boxes = _get_box_centers_please(line, edges)
        for box in boxes:
            x, y = box
            x = int(x)
            y = int(y)
            half_box_size = int(BOX_SIZE/2)
            cv.line(frame, (x - half_box_size, y - half_box_size), (x + half_box_size, y - half_box_size), color, 1)
            cv.line(frame, (x - half_box_size, y - half_box_size), (x - half_box_size, y + half_box_size), color, 1)
            cv.line(frame, (x + half_box_size, y + half_box_size), (x + half_box_size, y - half_box_size), color, 1)
            cv.line(frame, (x + half_box_size, y + half_box_size), (x - half_box_size, y + half_box_size), color, 1)
            # putting it on the contour image
            # cv.line(edges, (x - half_box_size, y - half_box_size), (x + half_box_size, y - half_box_size), (255, 255, 255), 1)
            # cv.line(edges, (x - half_box_size, y - half_box_size), (x - half_box_size, y + half_box_size), (255, 255, 255), 1)
            # cv.line(edges, (x + half_box_size, y + half_box_size), (x + half_box_size, y - half_box_size), (255, 255, 255), 1)
            # cv.line(edges, (x + half_box_size, y + half_box_size), (x - half_box_size, y + half_box_size), (255, 255, 255), 1)

def display_merged_lines_segments(merged_lines_segments, frame):
    merged_lines = list(merged_lines_segments.keys())
    for i in range(len(merged_lines)):
        line_segments = merged_lines_segments[merged_lines[i]]
        for j in range(len(line_segments)):
            color = (0, (255 - 255/len(merged_lines)*i) / 2, 255-255/len(merged_lines)*i)
            cv.line(frame, (line_segments[j].start_point[0],line_segments[j].start_point[1]), (line_segments[j].end_point[0],line_segments[j].end_point[1]), color, 2)


def display_tape_paths(tape_paths, frame):
    if tape_paths is None:
        return
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


def process_video():
    guard = True
    cap = cv.VideoCapture(0)
    img = np.zeros((25, 500, 3), np.uint8)
    cv.namedWindow('image')
    cv.createTrackbar('Blur', 'image', 5, 100, nothing)
    cv.createTrackbar('Block size', 'image', 5, 100, nothing)
    cv.createTrackbar('C', 'image', 5, 100, nothing)
    while cap.isOpened() and guard:
        ret, original_frame = cap.read()
        original_frame = cv.flip(original_frame, 1)
        original_frame = cv.rotate(original_frame, cv.ROTATE_90_CLOCKWISE)
        if not ret:
            print("Can't receive next frame")
            cap.set(cv.CAP_PROP_POS_FRAMES, 0)
            continue
        
        blur = cv.getTrackbarPos('Blur', 'image')
        block_size = cv.getTrackbarPos('Block size', 'image')
        c = cv.getTrackbarPos('C', 'image')
        processed_frame = process_frame(original_frame, blur, block_size, c)
        edges, houghlines = find_edges_and_lines(processed_frame)

        if isinstance(houghlines, np.ndarray):
            cv.putText(original_frame, f'lines: {len(houghlines)}', (0,50), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv.LINE_AA)

            lines = get_from_houghlines(houghlines)
            merged_lines = merge_lines(lines)
            merged_lines_segments = get_tape_corner_line_segments_please(merged_lines, edges)
            parallel_line_centers = get_centers_of_parallel_line_pairs(merged_lines)
            tape_segments = [x for l in list(merged_lines_segments.values()) for x in l]
            tape_paths = get_tape_paths(parallel_line_centers, tape_segments, original_frame)
            display_all_lines(lines, original_frame)
            display_merged_parallel_lines(merged_lines, original_frame)
            display_boxes_around_merged_lines(merged_lines, original_frame, edges)
            display_merged_lines_segments(merged_lines_segments, original_frame)
            display_center_of_parallel_lines(parallel_line_centers, original_frame)
            display_tape_paths(tape_paths, original_frame)
            display_displacement_and_direction_vectors(parallel_line_centers, original_frame)
            display_direction_to_go(parallel_line_centers, original_frame)

        cv.imshow('original video', original_frame)
        cv.imshow('processed video', processed_frame)
        cv.imshow('edges', edges)
        cv.imshow('image', img)
        cv.moveWindow('processed video', 700, 208)
        cv.moveWindow('edges', 1200, 208)
        if cv.waitKey(10) == ord('q'):
            guard = False
    cap.release()
    cv.destroyAllWindows()


if __name__ == "__main__":
    process_video()