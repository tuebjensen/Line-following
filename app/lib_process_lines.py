from math import cos, pi, sin, sqrt, tan
from statistics import median
import numpy as np

from lib_vector2d import Vector2D

BOX_SIZE= 20
PIXELS_THRESHOLD = 2*BOX_SIZE*0.5
MIN_LINE_SEGMENT_SIZE = 4
MIN_LINE_SEGMENT_HOLE_SIZE = 4

class Line:
    _rho_diff_threshold = 80.0
    _theta_diff_threshold = 0.3
    _end_point_distance_threshold = 50

    def __init__(self, rho: float, theta: float) -> 'Line':
        self.rho = rho
        self.theta = theta

    def is_similar(self, to_compare: 'Line', frame) -> bool:
        A, B = _get_line_frame_intersection_points(self, frame)
        C, D = _get_line_frame_intersection_points(to_compare, frame)
        AC = LineSegment(A, C)
        AD = LineSegment(A, D)
        BC = LineSegment(B, C)
        BD = LineSegment(B, D)
        length_1, length_2 = self._get_frame_intersection_distances(AC, AD, BC, BD)
        return length_1 < self._end_point_distance_threshold and length_2 < self._end_point_distance_threshold

    def _get_frame_intersection_distances(self, AC: 'LineSegment', AD: 'LineSegment', BC: 'LineSegment', BD: 'LineSegment'):
        len_AC = AC.get_length()
        len_AD = AD.get_length()
        len_BC = BC.get_length()
        len_BD = BD.get_length()
        return (len_AC, len_BD) if len_AC + len_BD <= len_BC + len_AD else (len_BC, len_AD)

class LineSegment:
    def __init__(self, start_point: 'tuple[int, int]', end_point: 'tuple[int, int]') -> 'LineSegment':
        self.start_point = start_point
        self.end_point = end_point

    def get_length(self):
        return sqrt((self.end_point[0] - self.start_point[0]) ** 2 + (self.end_point[1] - self.start_point[1]) ** 2)

    def get_direction_vector_please(self) -> 'Vector2D':
        return Vector2D(self.end_point[0]-self.start_point[0], self.end_point[1]-self.start_point[1])

    


def get_from_houghlines(hough_lines) -> 'list[Line]':
    if hough_lines is None:
        return None
    lines = []
    for line in hough_lines:
        rho, theta = line[0]
        lines.append(Line(rho, theta))
    return lines


def merge_lines(lines: 'list[Line]', frame) -> 'list[Line]':
    similar_lines: dict[Line, list[Line]] = {}
    for line in lines:
        found_similar = False
        for group_leading_line, grouped_lines in similar_lines.items():
            if line.is_similar(group_leading_line, frame):
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


def _get_tape_markers_please(white_pixels_per_box: 'list[int]') -> 'list[bool]':
    return [pixel_count > PIXELS_THRESHOLD for pixel_count in white_pixels_per_box]


def _get_filtered_markers_please(tape_markers: 'list[bool]') -> 'list[bool]':
    filtered_markers = _fill_gaps(tape_markers)
    filtered_markers = _filter_small_segments(filtered_markers)
    return filtered_markers


# TODO: probably don't need to fill up so aggressively, should rewrite
def _fill_gaps(tape_markers: 'list[bool]') -> 'list[bool]':
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


def _filter_small_segments(gap_filled_markers: 'list[bool]') -> 'list[bool]':
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


def _filter_segment_if_too_small(markers: 'list[bool]', segment_start: int, segment_end: int) -> 'list[bool]':
    if segment_start != None and segment_end - segment_start < MIN_LINE_SEGMENT_SIZE:
        markers[segment_start : segment_end + 1] = [False] * (segment_end - segment_start + 1)


def _get_line_segments_please(markers: 'list[bool]', centers: 'list[tuple[int, int]]') -> 'list[LineSegment]':
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


def get_tape_paths_and_lines(center_lines: 'list[Line]', tape_segments: 'list[LineSegment]', frame) -> 'dict[LineSegment, Line]':
    if(len(center_lines) != 2 ):
        return
    intersection_point = _get_intersection_point(center_lines[0], center_lines[1])
    center_line_segments = _segment_center_lines(center_lines, intersection_point, frame)
    tape_paths = _get_valid_center_line_segments(center_line_segments, tape_segments)
    return tape_paths


def _get_intersection_point(line_one: 'Line', line_two: 'Line') -> 'tuple[int, int]':
    """Finds the intersection of two lines given in Hesse normal form.

    Returns closest integer pixel locations.
    See https://stackoverflow.com/a/383527/5087436
    """
    rho1, theta1 = line_one.rho, line_one.theta
    rho2, theta2 = line_two.rho, line_two.theta
    A = np.array([
        [np.cos(theta1), np.sin(theta1)],
        [np.cos(theta2), np.sin(theta2)]
    ])
    b = np.array([[rho1], [rho2]])
    x0, y0 = np.linalg.solve(A, b)
    x0, y0 = int(np.round(x0)), int(np.round(y0))
    return (x0, y0)


def _segment_center_lines(center_lines: 'list[Line]', intersection_point: 'tuple[int, int]', frame) -> 'dict[LineSegment, Line]':
    center_line_segments = {}
    for center_line in center_lines:
        frame_intersection_points = _get_line_frame_intersection_points(center_line, frame)
        for frame_intersection_point in frame_intersection_points:
            line_segment = LineSegment(intersection_point, frame_intersection_point)
            center_line_segments[line_segment] = center_line
    return center_line_segments


def _get_line_frame_intersection_points(line: 'Line', frame) -> 'list[tuple[int, int]]':
    max_x = int(frame.shape[1] - 1)
    max_y = int(frame.shape[0] - 1)
    rho, theta = line.rho, line.theta
    x_intercept = int(rho*cos(theta) - rho*sin(theta)/tan(theta - pi/2))
    y_intercept = int(rho*sin(theta) - rho*cos(theta)*tan(theta - pi/2))
    possible_frame_intersection_points = [
        (0, y_intercept),
        (max_x, int(tan(theta - pi/2)*max_x + y_intercept)),
        (x_intercept, 0),
        (int(1/tan(theta - pi/2)*max_y + x_intercept), max_y)
    ]
    possible_frame_intersection_points = _filter_out_of_frame(possible_frame_intersection_points, max_x, max_y)
    frame_intersection_points = _filter_same_points(possible_frame_intersection_points)[0:2]
    return frame_intersection_points


def _filter_out_of_frame(possible_frame_intersection_points: 'list[tuple[int, int]]', max_x, max_y) -> 'list[tuple[int, int]]':
    filtered_points = []
    for possible_point in possible_frame_intersection_points:
        x, y = possible_point
        if x >= 0 and x <= max_x and y >= 0 and y <= max_y:
            filtered_points.append(possible_point)
    return filtered_points


def _filter_same_points(possible_frame_intersection_points: 'list[tuple[int, int]]') -> 'list[tuple[int, int]]':
    return list(set(possible_frame_intersection_points))


def _get_valid_center_line_segments(center_line_segments: 'dict[LineSegment, Line]', tape_segments: 'list[LineSegment]') -> 'dict[LineSegment, Line]':
    valid_center_line_segments = {}
    for center_line_segment in list(center_line_segments.keys()):
        valid = True
        for tape_segment in tape_segments:
            if _are_segments_intersecting(center_line_segment, tape_segment):
                valid = False
        if valid:
            valid_center_line_segments[center_line_segment] = center_line_segments[center_line_segment]
    return valid_center_line_segments


def _are_segments_intersecting(segment_one: 'LineSegment', segment_two: 'LineSegment') -> bool:
    A, B = segment_one.start_point, segment_one.end_point
    C, D = segment_two.start_point, segment_two.end_point
    return _intersect(A, B, C, D)


# https://stackoverflow.com/a/9997374
def _ccw(A,B,C) -> bool:
    Ax, Ay = A
    Bx, By = B
    Cx, Cy = C
    return (Cy-Ay) * (Bx-Ax) > (By-Ay) * (Cx-Ax)


# Return true if line segments AB and CD intersect
def _intersect(A,B,C,D) -> bool:
    return _ccw(A,C,D) != _ccw(B,C,D) and _ccw(A,B,C) != _ccw(A,B,D)
# https://stackoverflow.com/a/9997374


def _get_median_line(lines: 'list[Line]') -> 'Line':
    rhos = []
    thetas = []
    for line in lines:
        rho = line.rho
        theta = line.theta
        if(rho < 0):
            theta -= pi
            rho *= -1
        rhos.append(rho)
        thetas.append(theta)
    median_rho = median(rhos)
    median_theta = median(thetas)
    if median_theta < 0:
        median_theta += pi
        median_rho *= -1
    return Line(median_rho, median_theta)


def get_centers_of_parallel_line_pairs(lines: 'list[Line]') -> 'list[Line]':
    if lines is None:
        return None
    parallel_lines: dict[float, list[Line]] = {}
    for line in lines:
        found_parallel = False
        for parallel_line_angle, same_angle_lines in parallel_lines.items():
            if(abs(line.theta - parallel_line_angle) < Line._theta_diff_threshold 
                    or abs(line.theta - parallel_line_angle) > pi - Line._theta_diff_threshold):
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
    line_one = _convert_to_comparable_form(line_one)
    line_two = _convert_to_comparable_form(line_two)

    rho_one, theta_one = line_one.rho, line_one.theta
    rho_two, theta_two = line_two.rho, line_two.theta

    mean_rho = (rho_one + rho_two) / 2
    mean_theta = (theta_one + theta_two) / 2
    center_line = Line(mean_rho, mean_theta)
    center_line = _convert_to_conventional_form(center_line)

    return center_line


def _convert_to_comparable_form(line: 'Line') -> 'Line':
    rho, theta = line.rho, line.theta
    if(rho < 0):
        theta -= pi
        rho *= -1
    return Line(rho, theta)


def _convert_to_conventional_form(line: 'Line') -> 'Line':
    rho, theta = line.rho, line.theta
    if theta < 0:
        theta += pi
        rho *= -1
    return Line(rho, theta)