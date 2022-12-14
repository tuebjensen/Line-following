import random
import time
import cv2 as cv
import numpy as np
from lib_vector2d import Vector2D
from lib_lines_display import display_all_lines, display_boxes_around_merged_lines, display_center_of_parallel_lines, display_direction_to_go, display_displacement_and_direction_vectors, display_merged_lines_segments, display_merged_parallel_lines, display_tape_paths
from lib_calculate_direction import DirectionCalculator
from lib_process_lines import LineProcessor
from lib_image_processing import ImageProcessor


def nothing(x):
    pass


def process_video():
    guard = True
    cap = cv.VideoCapture(0)
    target_segment, target_line, current_node = None, None, None
    frames = 0
    start = time.time()
    image_processor = ImageProcessor(10, 5, 7, 85)
    line_processor = LineProcessor()
    direction_calculator = DirectionCalculator('W')
    while cap.isOpened() and guard:
        last_time = time.time()
        

        ret, original_frame = cap.read()
        # original_frame = cv.rotate(original_frame, cv.ROTATE_90_CLOCKWISE)
        original_frame = cv.flip(original_frame, -1)
        if not ret:
            print("Can't receive next frame")
            cap.set(cv.CAP_PROP_POS_FRAMES, 0)
            continue
        frames += 1
        
        processed_frame = image_processor._process_frame(original_frame)
        edges, houghlines = image_processor._find_edges_and_houghlines(processed_frame)
        opencv_processing_time = time.time() - last_time

        if isinstance(houghlines, np.ndarray):
            lines = line_processor._get_from_houghlines(houghlines)
            merged_lines = line_processor._merge_lines(lines, original_frame)
            merged_lines_segments = line_processor._get_tape_boundaries(merged_lines, edges)
            parallel_line_centers = line_processor._get_centers_of_parallel_line_pairs(merged_lines)
            tape_paths_and_lines = line_processor._get_tape_paths_and_lines(parallel_line_centers, merged_lines_segments, original_frame)
            display_all_lines(lines, original_frame)
            display_merged_parallel_lines(merged_lines, original_frame)
            display_boxes_around_merged_lines(merged_lines, original_frame, edges)
            display_merged_lines_segments(merged_lines_segments, original_frame)
            display_center_of_parallel_lines(parallel_line_centers, original_frame)
            display_tape_paths(tape_paths_and_lines, original_frame)

            target_segment, target_line, current_node = direction_calculator.decide_target(original_frame, tape_paths_and_lines)
            if target_segment is not None:
                displacement_vector = direction_calculator._get_displacement_vector_from_center(target_line, original_frame)
                direction_vector = target_segment.get_direction_vector()
                velocity_vector = direction_calculator._get_direction_to_go(displacement_vector, direction_vector, original_frame)
                display_displacement_and_direction_vectors(displacement_vector, direction_vector, original_frame)
                display_direction_to_go(velocity_vector, original_frame)
        cv.putText(original_frame, f'Frame: #{frames}, fps: {frames / (time.time() - start)}', (0,50), cv.FONT_HERSHEY_SIMPLEX, 1, (0,69,255), 2, cv.LINE_AA)
        cv.putText(original_frame, f'Stable: {DirectionCalculator.get_state_string(direction_calculator._stable_state)}', (0,80), cv.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2, cv.LINE_AA)
        cv.putText(original_frame, f'Incoming: {DirectionCalculator.get_state_string(direction_calculator._last_incoming_state)} x{direction_calculator._same_incoming_states_count}', (0,110), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv.LINE_AA)

        cv.imshow('original video', original_frame)
        cv.imshow('processed video', processed_frame)
        cv.imshow('edges', edges)
        cv.moveWindow('processed video', 700, 208)
        cv.moveWindow('edges', 1200, 208)
        if cv.waitKey(10) == ord('q'):
            guard = False
        
        total_time_to_process = time.time() - last_time
        #print(f'Total time to process: {round(total_time_to_process, 3)}, of which opencv was: {round(opencv_processing_time, 3)}')
    cap.release()
    cv.destroyAllWindows()





if __name__ == "__main__":
    # main()
    process_video()