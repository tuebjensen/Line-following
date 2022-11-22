from math import pi
import time
import cv2 as cv
import numpy as np
from lib_image_processing import find_edges_and_lines, nothing, process_frame
from lib_lines_display import display_all_lines, display_boxes_around_merged_lines, display_center_of_parallel_lines, display_direction_to_go, display_displacement_and_direction_vectors, display_merged_lines_segments, display_merged_parallel_lines, display_tape_paths
from lib_process_lines import Line, LineSegment, get_tape_paths_and_lines, get_centers_of_parallel_line_pairs, get_from_houghlines, get_tape_corner_line_segments_please, merge_lines, _get_intersection_point
from lib_calculate_direction import get_direction_to_go, get_displacement_vector_from_center

BLUR = 10
BLOCK_SIZE = 5
C = 3
HOUGH_THRESHOLD = 65
INTERSECTION_THRESHOLD = 0.3 # ratio of image height

STATE_FOLLOWING_LINE = 0
STATE_I_SEE_INTERSECTION = 1
STATE_TURNING = 2
STATE_STOP = 3
STATE_TURN180 = 4
STATE_IM_LOST = 5

STATE_CHANGE_THRESHOLD = 10
last_incoming_state = STATE_FOLLOWING_LINE
same_incoming_states_count = STATE_CHANGE_THRESHOLD
stable_state = STATE_FOLLOWING_LINE
last_target = None
last_line = None
command_list = ['R', 'S', 'L']
turning_just_initiated = False
close_my_eyes = False


def get_processed_frame(cap):
    target_segment, target_line = None, None
    last_time = time.time()
    

    ret, original_frame = cap.read()
    original_frame = cv.rotate(original_frame, cv.ROTATE_90_COUNTERCLOCKWISE)
    if not ret:
        print("Can't receive next frame")
        cap.set(cv.CAP_PROP_POS_FRAMES, 0)
        return ret, original_frame

    processed_frame = process_frame(original_frame, BLUR, BLOCK_SIZE, C)
    edges, houghlines = find_edges_and_lines(processed_frame, HOUGH_THRESHOLD)
    opencv_processing_time = time.time() - last_time

    if isinstance(houghlines, np.ndarray):
        cv.putText(original_frame, f'lines: {len(houghlines)}', (0,50), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv.LINE_AA)
        lines = get_from_houghlines(houghlines)                                                               #blue
        merged_lines = merge_lines(lines, original_frame)                                                     #green
        merged_lines_segments = get_tape_corner_line_segments_please(merged_lines, edges)                     #brown based on edge image, related to greens
        parallel_line_centers = get_centers_of_parallel_line_pairs(merged_lines)                              #red
        tape_segments = [x for l in list(merged_lines_segments.values()) for x in l]                          #brown by itself, no relationship with greens
        tape_paths_and_lines = get_tape_paths_and_lines(parallel_line_centers, tape_segments, original_frame) #purple
        display_all_lines(lines, original_frame)
        display_merged_parallel_lines(merged_lines, original_frame)
        display_boxes_around_merged_lines(merged_lines, original_frame, edges)
        display_merged_lines_segments(merged_lines_segments, original_frame)
        display_center_of_parallel_lines(parallel_line_centers, original_frame)
        display_tape_paths(tape_paths_and_lines, original_frame)

        target_segment, target_line = decide_target(original_frame, parallel_line_centers, tape_paths_and_lines, target_segment)
        if target_segment is not None:
            cv.putText(original_frame, _get_state_string(), (0,80), cv.FONT_HERSHEY_SIMPLEX, 1, (0,69,255), 2, cv.LINE_AA)
            displacement_vector = get_displacement_vector_from_center(target_line, original_frame)
            direction_vector = target_segment.get_direction_vector_please()
            velocity_vector = get_direction_to_go(displacement_vector, direction_vector, original_frame)
            display_displacement_and_direction_vectors(displacement_vector, direction_vector, original_frame)
            display_direction_to_go(velocity_vector, original_frame)
    
    total_time_to_process = time.time() - last_time
    print(f'Total time to process: {round(total_time_to_process, 3)}, of which opencv was: {round(opencv_processing_time, 3)}')
    return ret, original_frame


def process_video():
    guard = True
    cap = cv.VideoCapture(0)
    img = np.zeros((25, 500, 3), np.uint8)
    cv.namedWindow('image')
    cv.createTrackbar('Blur', 'image', BLUR, 100, nothing)
    cv.createTrackbar('Block size', 'image', BLOCK_SIZE, 100, nothing)
    cv.createTrackbar('C', 'image', C, 100, nothing)
    cv.createTrackbar('Threshold', 'image', HOUGH_THRESHOLD, 100, nothing)
    target_segment, target_line = None, None
    while cap.isOpened() and guard:
        last_time = time.time()
        

        ret, original_frame = cap.read()
        original_frame = cv.rotate(original_frame, cv.ROTATE_90_CLOCKWISE)
        if not ret:
            print("Can't receive next frame")
            cap.set(cv.CAP_PROP_POS_FRAMES, 0)
            continue
        
        blur = cv.getTrackbarPos('Blur', 'image')
        block_size = cv.getTrackbarPos('Block size', 'image')
        c = cv.getTrackbarPos('C', 'image')
        threshold = cv.getTrackbarPos('Threshold', 'image')
        processed_frame = process_frame(original_frame, blur, block_size, c)
        edges, houghlines = find_edges_and_lines(processed_frame, threshold)
        opencv_processing_time = time.time() - last_time

        if isinstance(houghlines, np.ndarray):
            cv.putText(original_frame, f'lines: {len(houghlines)}', (0,50), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv.LINE_AA)

            lines = get_from_houghlines(houghlines)                                                               #blue
            merged_lines = merge_lines(lines, original_frame)                                                     #green
            merged_lines_segments = get_tape_corner_line_segments_please(merged_lines, edges)                     #brown based on edge image, related to greens
            parallel_line_centers = get_centers_of_parallel_line_pairs(merged_lines)                              #red
            tape_segments = [x for l in list(merged_lines_segments.values()) for x in l]                          #brown by itself, no relationship with greens
            tape_paths_and_lines = get_tape_paths_and_lines(parallel_line_centers, tape_segments, original_frame) #purple
            display_all_lines(lines, original_frame)
            display_merged_parallel_lines(merged_lines, original_frame)
            display_boxes_around_merged_lines(merged_lines, original_frame, edges)
            display_merged_lines_segments(merged_lines_segments, original_frame)
            display_center_of_parallel_lines(parallel_line_centers, original_frame)
            display_tape_paths(tape_paths_and_lines, original_frame)

            target_segment, target_line = decide_target(original_frame, parallel_line_centers, tape_paths_and_lines, target_segment)
            if target_segment is not None:
                cv.putText(original_frame, _get_state_string(), (0,80), cv.FONT_HERSHEY_SIMPLEX, 1, (0,69,255), 2, cv.LINE_AA)
                displacement_vector = get_displacement_vector_from_center(target_line, original_frame)
                direction_vector = target_segment.get_direction_vector_please()
                velocity_vector = get_direction_to_go(displacement_vector, direction_vector, original_frame)
                display_displacement_and_direction_vectors(displacement_vector, direction_vector, original_frame)
                display_direction_to_go(velocity_vector, original_frame)
            

        cv.imshow('original video', original_frame)
        cv.imshow('processed video', processed_frame)
        cv.imshow('edges', edges)
        cv.imshow('image', img)
        cv.moveWindow('processed video', 700, 208)
        cv.moveWindow('edges', 1200, 208)
        if cv.waitKey(10) == ord('q'):
            guard = False
        
        total_time_to_process = time.time() - last_time
        print(f'Total time to process: {round(total_time_to_process, 3)}, of which opencv was: {round(opencv_processing_time, 3)}')
    cap.release()
    cv.destroyAllWindows()

def _get_state_string() -> str:
    global stable_state
    if stable_state == STATE_FOLLOWING_LINE:
        return 'Following line'
    if stable_state == STATE_I_SEE_INTERSECTION:
        return 'Intersection noticed, following line'
    if stable_state == STATE_TURNING:
        return 'Turning'
    if stable_state == STATE_STOP:
        return 'Stopped'
    if stable_state == STATE_TURN180:
        return 'Turning 180'
    if stable_state == STATE_IM_LOST:
        return 'Line lost'


def get_next_state(current_state, frame, parallel_line_centers, tape_paths_and_lines):
    count_paths = len(list(tape_paths_and_lines.keys()))
    next_state = None
    global turning_just_initiated
    if current_state == STATE_FOLLOWING_LINE:
        if count_paths > 1:
            intersection_red = _get_intersection_point(parallel_line_centers[0], parallel_line_centers[1])
            if intersection_red[1] > frame.shape[0]*INTERSECTION_THRESHOLD:
                next_state = STATE_TURNING
                turning_just_initiated = True
            else:
                next_state = STATE_I_SEE_INTERSECTION
        elif count_paths == 1:
            next_state = STATE_FOLLOWING_LINE   
        elif count_paths == 0:
            next_state = STATE_IM_LOST
    elif current_state == STATE_I_SEE_INTERSECTION:
        if count_paths > 1:
            intersection_red = _get_intersection_point(parallel_line_centers[0], parallel_line_centers[1])
            if intersection_red[1] > frame.shape[0]*INTERSECTION_THRESHOLD:
                next_state = STATE_TURNING
                turning_just_initiated = True
            else:
                next_state = STATE_I_SEE_INTERSECTION
        elif count_paths == 1:
            next_state = STATE_FOLLOWING_LINE
        elif count_paths == 0:
            next_state = STATE_IM_LOST
    elif current_state == STATE_TURNING:
        if count_paths > 1:
            next_state = STATE_TURNING
            turning_just_initiated = False
        elif count_paths == 1:
            next_state = STATE_FOLLOWING_LINE
        elif count_paths == 0:
            next_state = STATE_IM_LOST
    elif current_state == STATE_STOP:
        #some input has to go here if we wanna be able to get out of this state
        next_state = STATE_STOP
    elif current_state == STATE_TURN180:
        if count_paths > 1:
            next_state = STATE_TURN180
            print('Turned around and saw an intersection')
        elif count_paths == 1:
            if close_my_eyes == True:
                next_state = STATE_TURN180
            else:
                next_state = STATE_FOLLOWING_LINE
        elif count_paths == 0:
            close_my_eyes = False
            next_state = STATE_TURN180
    elif current_state == STATE_IM_LOST:
        if count_paths > 1:
            next_state = STATE_I_SEE_INTERSECTION
        elif count_paths == 1:
            next_state = STATE_FOLLOWING_LINE
        elif count_paths == 0:
            next_state = STATE_IM_LOST
    else:
        print(current_state)

    next_state = _get_stable_state(next_state)
    return next_state


def _get_stable_state(incoming_state):
    global stable_state
    global last_incoming_state
    global same_incoming_states_count

    if incoming_state != stable_state:
        if incoming_state == last_incoming_state:
            same_incoming_states_count += 1
            if same_incoming_states_count >= STATE_CHANGE_THRESHOLD:
                same_incoming_states_count = 1
                return incoming_state
        else :
            same_incoming_states_count = 1
        
        last_incoming_state = incoming_state
    else:
        return incoming_state

    return stable_state


def get_most_like(turning_direction: str, tape_paths_and_lines: 'dict[LineSegment, Line]') -> LineSegment:
    for path in list(tape_paths_and_lines.keys()):
        angle = path.get_direction_vector_please().get_angle()
        if ((turning_direction == 'R' and angle >= -pi/4 and angle <= pi/4)
                or (turning_direction == 'L' and ((angle >= 3*pi/4) or (angle <= -3*pi/4)))
                or (turning_direction == 'S' and angle >= -3*pi/4 and angle <= -pi/4)
                or (turning_direction == 'B' and angle >= pi/4 and angle <= 3*pi/4)):
            return path
       
    print('your map sucks')

def update_target(old_target: LineSegment, tape_paths_and_lines: 'dict[LineSegment, Line]') -> LineSegment:
    min_angle_dif = 2*pi
    min_angle_path = None
    for path in list(tape_paths_and_lines.keys()):
        angle_path = path.get_direction_vector_please().get_angle()
        angle_old = old_target.get_direction_vector_please().get_angle()
        angle_dif = abs(angle_old-angle_path)
        if angle_dif < min_angle_dif: 
            min_angle_dif = angle_dif
            min_angle_path = path
    return min_angle_path


def decide_target(original_frame, parallel_line_centers, tape_paths_and_lines, previous_target) -> LineSegment:
    global stable_state
    state = get_next_state(stable_state, original_frame, parallel_line_centers, tape_paths_and_lines)
    stable_state = state
    global last_target
    global last_line
    target = None
    line = None
    paths = list(tape_paths_and_lines.keys())
    if state == STATE_FOLLOWING_LINE:
        if(len(paths) == 1): # stable state
            target = paths[0]
            line = tape_paths_and_lines[target]
        if(len(paths) > 1): # transient state
            target = get_most_like('B', tape_paths_and_lines).flip()
            line = tape_paths_and_lines[target]
        if(len(paths) == 0): # transient state
            target = last_target
            line = last_line
    elif state == STATE_I_SEE_INTERSECTION:
        if(len(paths) > 1): # stable state
            target = get_most_like('B', tape_paths_and_lines).flip()
            line = tape_paths_and_lines[target]
        if(len(paths) <= 1): # transient state
            target = last_target
            line = last_line
    elif state == STATE_TURNING:
        if(len(paths) > 1): # stable state
            if turning_just_initiated: 
                turning_dir = command_list.pop(0) # TODO handle empty list
                target = get_most_like(turning_dir, tape_paths_and_lines)
                line = tape_paths_and_lines[target]
            else:
                target = update_target(previous_target, tape_paths_and_lines)
                line = tape_paths_and_lines[target]
        if(len(paths) <= 1): # transient state
            target = last_target
            line = last_line
    elif state == STATE_STOP:
        #some input has to go here if we wanna be able to get out of this state
        pass
    elif state == STATE_TURN180:
        pass 
    elif state == STATE_IM_LOST:
        target = None
        line = None
    last_target = target
    last_line = line
    return target, line



if __name__ == "__main__":
    # main()
    process_video()