from math import pi
import time
import cv2 as cv
import numpy as np
from lib_line_following import find_edges_and_lines, nothing, process_frame
from lib_lines_display import display_all_lines, display_boxes_around_merged_lines, display_center_of_parallel_lines, display_direction_to_go, display_displacement_and_direction_vectors, display_merged_lines_segments, display_merged_parallel_lines, display_tape_paths
from lib_process_lines import Line, LineSegment, get_tape_paths_and_lines, get_centers_of_parallel_line_pairs, get_from_houghlines, get_tape_corner_line_segments_please, merge_lines, _get_intersection_point
from lib_calculate_direction import get_direction_to_go, get_displacement_vector_from_center

BLUR = 10
BLOCK_SIZE = 5
C = 7
HOUGH_THRESHOLD = 65
INTERSECTION_THRESHOLD = 0.3 # ratio of image height

STATE_FOLLOWING_LINE = 0
STATE_I_SEE_INTERSECTION = 1
STATE_TURNING = 2
STATE_STOP = 3
STATE_TURN180 = 4
STATE_IM_LOST = 5

turning_just_initiated = False
current_state = STATE_FOLLOWING_LINE
target = None
close_my_eyes = False


def process_video():
    guard = True
    cap = cv.VideoCapture(0)
    img = np.zeros((25, 500, 3), np.uint8)
    cv.namedWindow('image')
    cv.createTrackbar('Blur', 'image', 10, 100, nothing)
    cv.createTrackbar('Block size', 'image', 5, 100, nothing)
    cv.createTrackbar('C', 'image', 7, 100, nothing)
    cv.createTrackbar('Threshold', 'image', 100, 100, nothing)
    target = None
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
        print(f'Hough transform time to process: {time.time() - last_time}')

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

            # target = decide_target(original_frame, parallel_line_centers, tape_paths_and_lines, target)
            # if target is not None:
            #     displacement_vector = get_displacement_vector_from_center(tape_paths_and_lines[target], original_frame)
            #     direction_vector = target.get_direction_vector_please()
            #     velocity_vector = get_direction_to_go(displacement_vector, direction_vector, original_frame)
            #     display_displacement_and_direction_vectors(displacement_vector, direction_vector, original_frame)
            #     display_direction_to_go(velocity_vector, original_frame)
            

        cv.imshow('original video', original_frame)
        cv.imshow('processed video', processed_frame)
        cv.imshow('edges', edges)
        cv.imshow('image', img)
        cv.moveWindow('processed video', 700, 208)
        cv.moveWindow('edges', 1200, 208)
        if cv.waitKey(10) == ord('q'):
            guard = False
        
        print(f'Total time to process: {time.time() - last_time}')
    cap.release()
    cv.destroyAllWindows()


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
            print('fuck your stupid map')
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
        print('i died')
    return next_state

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

    
command_list = ['R', 'S', 'L']

def decide_target(original_frame, parallel_line_centers, tape_paths_and_lines, previous_target) -> LineSegment:
    global current_state
    state = get_next_state(current_state, original_frame, parallel_line_centers, tape_paths_and_lines)
    current_state = state
    target = None
    if state == STATE_FOLLOWING_LINE:
        target = list(tape_paths_and_lines.keys())[0]
    elif state == STATE_I_SEE_INTERSECTION:
        target = get_most_like('B', tape_paths_and_lines).flip()
    elif state == STATE_TURNING:
        if turning_just_initiated:
            turning_dir = command_list.pop(0) # TODO handle empty list
            target = get_most_like(turning_dir, tape_paths_and_lines)
        else:
            target = update_target(previous_target, tape_paths_and_lines)
    elif state == STATE_STOP:
        #some input has to go here if we wanna be able to get out of this state
        pass
    elif state == STATE_TURN180:
        pass 
    elif state == STATE_IM_LOST:
        pass
    return target

# class ProcessedFrameInfo:
#     def __init__(self,
#                 frame,
#                 edges,
#                 lines: 'list[Line]',
#                 merged_lines: 'list[Line]',
#                 merged_lines_segments: 'dict[Line, LineSegment]',
#                 parallel_line_centers: 'list[Line]',
#                 tape_paths_and_lines: 'dict[LineSegment, Line]') -> 'ProcessedFrameInfo':
#         self.frame = frame
#         self.edges = edges
#         self.lines = lines
#         self.merged_lines = merged_lines
#         self.merged_lines_segments = merged_lines_segments
#         self.tape_segments = [x for l in list(merged_lines_segments.values()) for x in l]
#         self.parallel_line_centers = parallel_line_centers
#         self.tape_paths_and_lines = tape_paths_and_lines
#         self.tape_paths = list(tape_paths_and_lines.keys())

# def process_one_frame(capture):
#     original_frame = get_frame(capture)
#     if original_frame is None:
#         capture.set(cv.CAP_PROP_POS_FRAMES, 0)
#         return
#     original_frame = cv.flip(original_frame, 1)
#     original_frame = cv.rotate(original_frame, cv.ROTATE_90_CLOCKWISE)

#     processed_frame = process_frame(original_frame, BLUR, BLOCK_SIZE, C)
#     edges, houghlines = find_edges_and_lines(processed_frame, HOUGH_THRESHOLD)
#     if not isinstance(houghlines, np.ndarray):
#         return

#     lines = get_from_houghlines(houghlines)                                                               #blue
#     merged_lines = merge_lines(lines, original_frame)                                                     #green
#     merged_lines_segments = get_tape_corner_line_segments_please(merged_lines, edges)                     #brown based on edge image, related to greens
#     parallel_line_centers = get_centers_of_parallel_line_pairs(merged_lines)                              #red
#     tape_segments = [x for l in list(merged_lines_segments.values()) for x in l]                          #brown by itself, no relationship with greens
#     tape_paths_and_lines = get_tape_paths_and_lines(parallel_line_centers, tape_segments, original_frame) #purple

#     return ProcessedFrameInfo(original_frame, edges, lines, merged_lines, merged_lines_segments, parallel_line_centers, tape_paths_and_lines)
    

# def display_processed_info(processed_frame_info: ProcessedFrameInfo):
#     if processed_frame_info is None:
#         return
#     original_frame = processed_frame_info.frame
#     edges = processed_frame_info.edges
#     lines = processed_frame_info.lines
#     merged_lines = processed_frame_info.merged_lines
#     merged_lines_segments = processed_frame_info.merged_lines_segments
#     parallel_line_centers = processed_frame_info.parallel_line_centers
#     tape_paths_and_lines = processed_frame_info.tape_paths_and_lines
#     display_all_lines(lines, original_frame)
#     display_merged_parallel_lines(merged_lines, original_frame)
#     display_boxes_around_merged_lines(merged_lines, original_frame, edges)
#     display_merged_lines_segments(merged_lines_segments, original_frame)
#     display_center_of_parallel_lines(parallel_line_centers, original_frame)
#     display_tape_paths(tape_paths_and_lines, original_frame)
#     # cv.imshow('original video', original_frame)


# def get_frame(capture):
#     if capture.isOpened():
#         ret, original_frame = capture.read()
#         if ret:
#             return original_frame


# def main():
#     guard = True
#     capture = cv.VideoCapture(0)
#     img = np.zeros((25, 500, 3), np.uint8)
#     cv.namedWindow('image')
#     cv.createTrackbar('Blur', 'image', 10, 100, nothing)
#     cv.createTrackbar('Block size', 'image', 5, 100, nothing)
#     cv.createTrackbar('C', 'image', 7, 100, nothing)
#     cv.createTrackbar('Threshold', 'image', 100, 100, nothing)
#     while capture.isOpened() and guard:
#         ret, original_frame = capture.read()
#         original_frame = cv.flip(original_frame, 1)
#         original_frame = cv.rotate(original_frame, cv.ROTATE_90_CLOCKWISE)
#         if not ret:
#             print("Can't receive next frame")
#             capture.set(cv.CAP_PROP_POS_FRAMES, 0)
#             continue
        
#         blur = cv.getTrackbarPos('Blur', 'image')
#         block_size = cv.getTrackbarPos('Block size', 'image')
#         c = cv.getTrackbarPos('C', 'image')
#         threshold = cv.getTrackbarPos('Threshold', 'image')
#         processed_frame = process_frame(original_frame, blur, block_size, c)
#         edges, houghlines = find_edges_and_lines(processed_frame, threshold)

#         if isinstance(houghlines, np.ndarray):
#             cv.putText(original_frame, f'lines: {len(houghlines)}', (0,50), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv.LINE_AA)

#             processed_frame_info = process_one_frame(capture)
#             display_processed_info(processed_frame_info)
#             print("Frame processed")

#         cv.imshow('original video', original_frame)
#         cv.imshow('processed video', processed_frame)
#         cv.imshow('edges', edges)
#         cv.imshow('image', img)
#         cv.moveWindow('processed video', 700, 208)
#         cv.moveWindow('edges', 1200, 208)
#         if cv.waitKey(10) == ord('q'):
#             guard = False
#     capture.release()
#     cv.destroyAllWindows()
        


if __name__ == "__main__":
    # main()
    process_video()