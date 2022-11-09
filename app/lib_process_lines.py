from math import cos, pi, sin, tan
from statistics import median
from typing import Union

BOX_SIZE= 20
PIXELS_THRESHOLD = 2*BOX_SIZE*0.75
MIN_LINE_SEGMENT_SIZE = 4
MIN_LINE_SEGMENT_HOLE_SIZE = 4

class Line:
    _rho_diff_threshold = 80.0
    _theta_diff_threshold = 0.3

    def __init__(self, rho: float, theta: float) -> 'Line':
        self.rho = rho
        self.theta = theta

    def is_similar(self, to_compare: 'Line') -> bool:
        return (abs(self.rho - to_compare.rho) < self._rho_diff_threshold 
                and abs(self.theta - to_compare.theta) < self._theta_diff_threshold)

class LineSegment:
    def __init__(self, start_point: 'tuple[int, int]', end_point: 'tuple[int, int]') -> 'LineSegment':
        self.start_point = start_point
        self.end_point = end_point


def get_from_houghlines(hough_lines) -> 'list[Line]':
    if hough_lines is None:
        return None
    lines = []
    for line in hough_lines:
        rho, theta = line[0]
        lines.append(Line(rho, theta))
    return lines


def merge_lines(lines: 'list[Line]') -> 'list[Line]':
    similar_lines: dict[Line, list[Line]] = {}
    for line in lines:
        found_similar = False
        for group_leading_line, grouped_lines in similar_lines.items():
            if line.is_similar(group_leading_line):
                found_similar = True
                grouped_lines.append(line)
                break
        if not found_similar:
            similar_lines[line] = [line]

    merged_lines = []
    for grouped_lines in list(similar_lines.values()):
        merged_lines.append(_get_median_line(grouped_lines))
    return merged_lines


def get_tape_corner_line_segments_please(merged_lines: 'list[Line]', edges) -> 'dict[Line, list[LineSegment]]':
    lines_segments: dict[Line, list[LineSegment]] = {}
    for line in merged_lines:
        box_centers = _get_box_centers_please(line, edges)
        white_pixels_per_box = _get_white_pixels_per_box_please(box_centers, edges)
        tape_markers = _get_tape_markers_please(white_pixels_per_box)
        filtered_markers = _get_filtered_markers_please(tape_markers)
        lines_segments[line] = _get_line_segments_please(filtered_markers, box_centers)
    return lines_segments

def _get_box_centers_please(line:'Line', edges) -> 'list[tuple[int,int]]':
    box_centers = []
    max_x = edges.shape[1]
    max_y = edges.shape[0]
    rho, theta = line.rho, line.theta
    iterate_along_x_axis = _is_line_more_horizontal_please(line)
    delta_x = BOX_SIZE if iterate_along_x_axis else BOX_SIZE * 1/tan(theta - pi/2)
    delta_y = BOX_SIZE if not iterate_along_x_axis else BOX_SIZE * tan(theta - pi/2)
    x_intercept = rho*cos(theta) - rho*sin(theta)/tan(theta - pi/2)
    y_intercept = rho*sin(theta) - rho*cos(theta)*tan(theta - pi/2)

    box_count = int(max_x / BOX_SIZE if iterate_along_x_axis else max_y / BOX_SIZE)

    for i in range(box_count):
        x = i * delta_x if iterate_along_x_axis else round(x_intercept + i*delta_x)
        y = i * delta_y if not iterate_along_x_axis else round(y_intercept + i*delta_y)
        if y >= 0 and y < max_y and x >= 0 and x <= max_x:
            box_centers.append((x, y))
    return box_centers

def _is_line_more_horizontal_please(line:'Line') -> bool:
    return line.theta >= pi/4 and line.theta <= 3*pi/4

def _get_white_pixels_per_box_please(box_centers: 'list[tuple[int,int]]', edges) -> 'list[int]':
    max_x = edges.shape[1]
    max_y = edges.shape[0]
    pixels_per_box = []
    half_box_size = int(BOX_SIZE / 2)
    for (x, y) in box_centers:
        pixels_count = 0
        for delta_x in range(-half_box_size, half_box_size):
            for delta_y in range(-half_box_size, half_box_size):
                if (x + delta_x > 0 and x + delta_x < max_x
                        and y + delta_y > 0 and y + delta_y < max_y
                        and edges[y + delta_y, x + delta_x] == 255):
                    pixels_count += 1
        pixels_per_box.append(pixels_count)
    return pixels_per_box

def _get_tape_markers_please(white_pixels_per_box: 'list[int]'):
    return [pixel_count > PIXELS_THRESHOLD for pixel_count in white_pixels_per_box]


def _get_filtered_markers_please(tape_markers):
    filtered_markers = _fill_gaps(tape_markers)
    filtered_markers = _filter_small_segments(filtered_markers)
    return filtered_markers

def _fill_gaps(tape_markers):
    look_forward_amount = MIN_LINE_SEGMENT_HOLE_SIZE - 1
    gap_filled_markers = tape_markers.copy()
    recording = False
    current_segment_size = 0
    i = -1
    while i < len(tape_markers) - 1:
        i += 1
        if tape_markers[i] is True:
            recording = True
            current_segment_size += 1
        elif recording is True and tape_markers[i] is False:
            markers_forward = 0
            end_index = i
            for j in range(1, look_forward_amount + 1):
                if (i + j < len(tape_markers) - 1
                        and tape_markers[i + j] == True):
                    markers_forward += 1
                    end_index = i + j
            if markers_forward == 0:
                i += look_forward_amount
                current_segment_size = 0
                recording = False
            elif current_segment_size + markers_forward + 1 >= MIN_LINE_SEGMENT_HOLE_SIZE:
                gap_filled_markers[i : end_index + 1] = [True] * (end_index - i + 1)
                current_segment_size += end_index - i
                i = end_index - 1 # -1 because incrementing is the first step of the loop
    return gap_filled_markers

def _filter_small_segments(gap_filled_markers):
    filtered_markers = gap_filled_markers.copy()
    i = 0
    while i < len(gap_filled_markers) - 1:
        start, end = _get_next_segments_indices(gap_filled_markers, i)
        _filter_segment_if_too_small(filtered_markers, start, end)
        i = i+1 if end is None else end
    return filtered_markers

def _get_next_segments_indices(markers: 'list[bool]', start_from: int) -> 'tuple[int, int]':
    segment_started = False
    start_index = None
    end_index = None
    for i in range(start_from, len(markers)):
        if segment_started is False and markers[i] is True:
            segment_started = True
            start_index = i
        if segment_started and markers[i] is False:
            segment_started = False
            end_index = i
            break
    return start_index, end_index or (None if start_index is None else len(markers) - 1)

def _filter_segment_if_too_small(markers, segment_start, segment_end):
    if segment_start != None and segment_end - segment_start < MIN_LINE_SEGMENT_SIZE:
        markers[segment_start : segment_end + 1] = [False] * (segment_end - segment_start + 1)

def _get_line_segments_please(markers, centers):
    line_segments = []
    search_from = 0
    while search_from is not None:
        start, end = _get_next_segments_indices(markers, search_from)
        if start is not None:
            start_x, start_y = centers[start]
            end_x, end_y = centers[end]
            line_segments.append(LineSegment((start_x, start_y), (end_x, end_y)))
        search_from = None if end is None else end + 1
    return line_segments


def _get_median_line(lines: 'list[Line]') -> 'Line':
    rhos = []
    thetas = []
    for line in lines:
        rhos.append(line.rho)
        thetas.append(line.theta)
    median_rho = median(rhos)
    median_theta = median(thetas)
    return Line(median_rho, median_theta)


def get_centers_of_parallel_line_pairs(lines: 'list[Line]') -> 'list[Line]':
    if lines is None:
        return None
    parallel_lines: dict[float, list[Line]] = {}
    for line in lines:
        found_parallel = False
        for parallel_line_angle, same_angle_lines in parallel_lines.items():
            if(abs(line.theta - parallel_line_angle) < 2*Line._theta_diff_threshold):
                same_angle_lines.append(line)
                found_parallel = True
                break
        if not found_parallel:
            parallel_lines[line.theta] = [line]

    center_lines: list[Line] = []
    for same_angle_lines in list(parallel_lines.values()):
        if(len(same_angle_lines) == 2):
            center_lines.append(_get_center_line(same_angle_lines[0], same_angle_lines[1]))

    return center_lines


def _get_center_line(line_one: 'Line', line_two: 'Line') -> 'Line':
    mean_rho = (line_one.rho + line_two.rho) / 2
    mean_theta = (line_one.theta + line_two.theta) / 2
    return Line(mean_rho, mean_theta)
