import time
import cv2 as cv
import numpy as np
from lib_vector2d import Vector2D
from lib_lines_display import display_all_lines, display_boxes_around_merged_lines, display_center_of_parallel_lines, display_direction_to_go, display_displacement_and_direction_vectors, display_merged_lines_segments, display_merged_parallel_lines, display_tape_paths
from lib_calculate_direction import DirectionCalculator
from lib_process_lines import LineProcessor
from lib_image_processing import ImageProcessor

frames = 0
start = time.time()


def get_processed_frame_and_direction_vector(original_frame,
        image_processor: ImageProcessor,
        line_processor: LineProcessor,
        direction_calculator: DirectionCalculator):

    fstart = time.time()
    
    #print(direction_calculator)
    global frames
    global start
    frames += 1
    # original_frame = original_frame[:,30:]
    # original_frame = cv.rotate(original_frame, cv.ROTATE_90_CLOCKWISE)
    print('processing-part-1', fstart - time.time())
    original_frame = cv.flip(original_frame, -1)
    print('processing-part-2', fstart - time.time())
    edges, houghlines = image_processor.get_edges_and_houghlines(original_frame)
    print('processing-part-3', fstart - time.time())
    tape_paths = line_processor.get_tape_paths(original_frame, edges, houghlines)
    print('processing-part-4', fstart - time.time())
    velocity_vector = Vector2D(0, 0)
    current_node = None

    if isinstance(houghlines, np.ndarray):
        lines = line_processor._get_from_houghlines(houghlines)
        print('processing-part-5', fstart - time.time())
        merged_lines = line_processor._merge_lines(lines, original_frame)
        print('processing-part-6', fstart - time.time())
        merged_lines_segments = line_processor._get_tape_boundaries(merged_lines, edges)
        print('processing-part-7', fstart - time.time())
        parallel_line_centers = line_processor._get_centers_of_parallel_line_pairs(merged_lines)
        print('processing-part-8', fstart - time.time())
        tape_paths = line_processor._get_tape_paths_and_lines(parallel_line_centers, merged_lines_segments, original_frame)
        print('processing-part-9', fstart - time.time())
        display_all_lines(lines, original_frame)
        display_merged_parallel_lines(merged_lines, original_frame)
        display_boxes_around_merged_lines(merged_lines, original_frame, edges)
        display_merged_lines_segments(merged_lines_segments, original_frame)
        display_center_of_parallel_lines(parallel_line_centers, original_frame)
        display_tape_paths(tape_paths, original_frame)
        print('processing-part-10', fstart - time.time())

    target_segment, target_line, current_node = direction_calculator.decide_target(
                                                            original_frame,
                                                            tape_paths)
    print('processing-part-11', fstart - time.time())

    if target_segment is not None:
        displacement_vector = direction_calculator._get_displacement_vector_from_center(target_line, original_frame)
        print('processing-part-12', fstart - time.time())
        direction_vector = target_segment.get_direction_vector_please()
        print('processing-part-13', fstart - time.time())
        velocity_vector = direction_calculator._get_direction_to_go(displacement_vector, direction_vector, original_frame)
        print('processing-part-14', fstart - time.time())
        display_displacement_and_direction_vectors(displacement_vector, direction_vector, original_frame)
        display_direction_to_go(velocity_vector, original_frame)
        print('processing-part-15', fstart - time.time())

    cv.putText(original_frame, f'Frame: #{frames}, fps: {(frames / (time.time() - start)):.2f}', (0,50), cv.FONT_HERSHEY_SIMPLEX, 1, (0,69,255), 2, cv.LINE_AA)
    cv.putText(original_frame, f'Stable: {direction_calculator.get_state_string(direction_calculator._stable_state)}', (0,80), cv.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2, cv.LINE_AA)
    cv.putText(original_frame, f'Incoming: {direction_calculator.get_state_string(direction_calculator._last_incoming_state)} x{direction_calculator._same_incoming_states_count}', (0,110), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv.LINE_AA)
    print('processing-part-16', fstart - time.time())

    return {
        'frame': original_frame,
        'velocity_vector': (-velocity_vector.x, -velocity_vector.y),
        'current_node': current_node,
        'direction_calculator': direction_calculator
    }