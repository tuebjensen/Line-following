from math import pi
import time
import cv2 as cv
import numpy as np
from lib_lines_display import display_all_lines, display_boxes_around_merged_lines, display_center_of_parallel_lines, display_direction_to_go, display_displacement_and_direction_vectors, display_merged_lines_segments, display_merged_parallel_lines, display_tape_paths
from lib_calculate_direction import DirectionCalculator
from lib_process_lines import LineProcessor
from lib_image_processing import ImageProcessor

camera = cv.VideoCapture(0)
image_processor = ImageProcessor()
line_processor = LineProcessor()
direction_calculator = DirectionCalculator('W')


STATE_FOLLOWING_LINE = 0
STATE_I_SEE_INTERSECTION = 1
STATE_TURNING = 2
STATE_STOP = 3
STATE_TURN180 = 4
STATE_IM_LOST = 5


def get_processed_frame(original_frame):
    ret, original_frame = camera.read()
    original_frame = original_frame[:,30:]
    original_frame = cv.rotate(original_frame, cv.ROTATE_90_CLOCKWISE)
    edges, houghlines = image_processor.get_edges_and_houghlines(original_frame)
    tape_paths = line_processor.get_tape_paths(original_frame, edges, houghlines)
    direction_vector = direction_calculator.get_direction_vector(tape_paths)

    if isinstance(houghlines, np.ndarray):
        cv.putText(original_frame, f'lines: {len(houghlines)}', (0,50), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv.LINE_AA)
        lines = line_processor._get_from_houghlines(houghlines)
        merged_lines = line_processor._merge_lines(lines, original_frame)
        merged_lines_segments = line_processor._get_tape_boundaries(merged_lines, edges)
        parallel_line_centers = line_processor._get_centers_of_parallel_line_pairs(merged_lines)
        tape_segments = [x for l in list(merged_lines_segments.values()) for x in l]
        tape_paths_and_lines = line_processor._get_tape_paths_and_lines(parallel_line_centers, tape_segments, original_frame)
        display_all_lines(lines, original_frame)
        display_merged_parallel_lines(merged_lines, original_frame)
        display_boxes_around_merged_lines(merged_lines, original_frame, edges)
        display_merged_lines_segments(merged_lines_segments, original_frame)
        display_center_of_parallel_lines(parallel_line_centers, original_frame)
        display_tape_paths(tape_paths_and_lines, original_frame)

        target_segment, target_line = direction_calculator._decide_target(
                                                                original_frame,
                                                                parallel_line_centers,
                                                                tape_paths_and_lines)
        if target_segment is not None:
            cv.putText(original_frame, _get_state_string(), (0,80), cv.FONT_HERSHEY_SIMPLEX, 1, (0,69,255), 2, cv.LINE_AA)
            displacement_vector = direction_calculator._get_displacement_vector_from_center(target_line, original_frame)
            direction_vector = target_segment.get_direction_vector_please()
            velocity_vector = direction_calculator._get_direction_to_go(displacement_vector, direction_vector, original_frame)
            display_displacement_and_direction_vectors(displacement_vector, direction_vector, original_frame)
            display_direction_to_go(velocity_vector, original_frame)
    
    return original_frame, (-velocity_vector.x, -velocity_vector.y)

def nothing():
    pass

def process_video():
    guard = True
    cap = cv.VideoCapture(0)
    img = np.zeros((25, 500, 3), np.uint8)
    cv.namedWindow('image')
    cv.createTrackbar('Blur', 'image', 10, 100, nothing)
    cv.createTrackbar('Block size', 'image', 5, 100, nothing)
    cv.createTrackbar('C', 'image', 3, 100, nothing)
    cv.createTrackbar('Threshold', 'image', 65, 100, nothing)
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
        processed_frame = image_processor._process_frame(original_frame, blur, block_size, c)
        edges, houghlines = image_processor._find_edges_and_houghlines(processed_frame, threshold)
        opencv_processing_time = time.time() - last_time

        if isinstance(houghlines, np.ndarray):
            cv.putText(original_frame, f'lines: {len(houghlines)}', (0,50), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv.LINE_AA)

            lines = line_processor._get_from_houghlines(houghlines)                                                               #blue
            merged_lines = line_processor._merge_lines(lines, original_frame)                                                     #green
            merged_lines_segments = line_processor._get_tape_boundaries(merged_lines, edges)                     #brown based on edge image, related to greens
            parallel_line_centers = line_processor._get_centers_of_parallel_line_pairs(merged_lines)                              #red
            tape_segments = [x for l in list(merged_lines_segments.values()) for x in l]                          #brown by itself, no relationship with greens
            tape_paths_and_lines = line_processor._get_tape_paths_and_lines(parallel_line_centers, tape_segments, original_frame) #purple
            display_all_lines(lines, original_frame)
            display_merged_parallel_lines(merged_lines, original_frame)
            display_boxes_around_merged_lines(merged_lines, original_frame, edges)
            display_merged_lines_segments(merged_lines_segments, original_frame)
            display_center_of_parallel_lines(parallel_line_centers, original_frame)
            display_tape_paths(tape_paths_and_lines, original_frame)

            target_segment, target_line = direction_calculator._decide_target(original_frame, parallel_line_centers, tape_paths_and_lines, target_segment)
            if target_segment is not None:
                cv.putText(original_frame, _get_state_string(), (0,80), cv.FONT_HERSHEY_SIMPLEX, 1, (0,69,255), 2, cv.LINE_AA)
                displacement_vector = direction_calculator._get_displacement_vector_from_center(target_line, original_frame)
                direction_vector = target_segment.get_direction_vector_please()
                velocity_vector = direction_calculator._get_direction_to_go(displacement_vector, direction_vector, original_frame)
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
        #print(f'Total time to process: {round(total_time_to_process, 3)}, of which opencv was: {round(opencv_processing_time, 3)}')
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



if __name__ == "__main__":
    # main()
    process_video()