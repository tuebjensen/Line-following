from math import cos, pi, sin, sqrt, tan
from statistics import median
import numpy as np
from lib_vector2d import Vector2D



class Line:
    _rho_diff_threshold = 80.0
    _theta_diff_threshold = 0.3
    _distance_threshold = 40

    def __init__(self, rho: float, theta: float) -> 'Line':
        self.rho = rho
        self.theta = theta

    def is_similar(self, to_compare: 'Line', frame) -> bool:
        A, B = _get_line_frame_intersection_points(self, frame)
        C, D = _get_line_frame_intersection_points(to_compare, frame)
        AB = LineSegment(A, B)
        CD = LineSegment(C, D)

        dist_A_to_CD = self._distance_from_point_to_line_segment(A, CD)
        dist_B_to_CD = self._distance_from_point_to_line_segment(B, CD)
        dist_C_to_AB = self._distance_from_point_to_line_segment(C, AB)
        dist_D_to_AB = self._distance_from_point_to_line_segment(D, AB)
        
        return (dist_A_to_CD < self._distance_threshold
                and dist_B_to_CD < self._distance_threshold
                and dist_C_to_AB < self._distance_threshold
                and dist_D_to_AB < self._distance_threshold)

    def _distance_from_point_to_line_segment(self, point: 'tuple[int, int]', line_segment: 'LineSegment') -> float:
        x0, y0 = point
        x1, y1 = line_segment.start_point
        x2, y2 = line_segment.end_point
        return abs((x2-x1)*(y1-y0) - (x1-x0)*(y2-y1)) / sqrt((x2-x1)**2 + (y2-y1)**2)



class LineSegment:
    def __init__(self, start_point: 'tuple[int, int]', end_point: 'tuple[int, int]') -> 'LineSegment':
        self.start_point = start_point
        self.end_point = end_point

    def get_length(self):
        return sqrt((self.end_point[0] - self.start_point[0]) ** 2 + (self.end_point[1] - self.start_point[1]) ** 2)

    def get_direction_vector_please(self) -> 'Vector2D':
        return Vector2D(self.end_point[0]-self.start_point[0], self.end_point[1]-self.start_point[1])

    def flip(self) -> 'LineSegment':
        temp = self.start_point
        self.start_point = self.end_point
        self.end_point = temp
        return self



class LineProcessor:
    def __init__(self, box_size=20, pixels_threshold=20, min_line_segment_size=3, min_line_segment_hole_size=2):
        self._BOX_SIZE = box_size
        self._PIXELS_THRESHOLD = pixels_threshold
        self._MIN_LINE_SEGMENT_SIZE = min_line_segment_size
        self._MIN_LINE_SEGMENT_HOLE_SIZE = min_line_segment_hole_size


    def get_tape_paths(self, frame, edges, houghlines) -> 'dict[LineSegment, Line]':
        lines = self._get_from_houghlines(houghlines)
        merged_lines = self._merge_lines(lines, frame)
        tape_boundaries = self._get_tape_boundaries(merged_lines, edges)
        parallel_line_centers = self._get_centers_of_parallel_line_pairs(merged_lines)
        tape_paths = self._get_tape_paths_and_lines(parallel_line_centers, tape_boundaries, frame)
        return tape_paths


    def _get_from_houghlines(self, hough_lines) -> 'list[Line]':
        if hough_lines is None:
            return []
        lines = []
        for line in hough_lines:
            rho, theta = line[0]
            lines.append(Line(rho, theta))
        return lines


    def _merge_lines(self, lines: 'list[Line]', frame) -> 'list[Line]':
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
            merged_lines.append(self._get_median_line(grouped_lines))
        return merged_lines


    def _get_tape_boundaries(self, merged_lines: 'list[Line]', edges) -> 'dict[Line, list[LineSegment]]':
        lines_segments: dict[Line, list[LineSegment]] = {}
        for line in merged_lines:
            box_centers = self._get_box_centers_please(line, edges)
            white_pixels_per_box = self._get_white_pixels_per_box_please(box_centers, edges)
            tape_markers = self._get_tape_markers_please(white_pixels_per_box)
            filtered_markers = self._get_filtered_markers_please(tape_markers)
            lines_segments[line] = self._get_line_segments_please(filtered_markers, box_centers)
        return lines_segments


    def _get_box_centers_please(self, line:'Line', edges) -> 'list[tuple[int,int]]':
        box_centers = []
        max_x = edges.shape[1]
        max_y = edges.shape[0]
        rho, theta = line.rho, line.theta
        iterate_along_x_axis = self._is_line_more_horizontal_please(line)
        delta_x = self._BOX_SIZE if iterate_along_x_axis else self._BOX_SIZE * 1/tan(theta - pi/2)
        delta_y = self._BOX_SIZE if not iterate_along_x_axis else self._BOX_SIZE * tan(theta - pi/2)
        x_intercept = rho*cos(theta) - rho*sin(theta)/tan(theta - pi/2)
        y_intercept = rho*sin(theta) - rho*cos(theta)*tan(theta - pi/2)

        box_count = int(max_x / self._BOX_SIZE if iterate_along_x_axis else max_y / self._BOX_SIZE)

        for i in range(box_count):
            x = i * delta_x if iterate_along_x_axis else round(x_intercept + i*delta_x)
            y = i * delta_y if not iterate_along_x_axis else round(y_intercept + i*delta_y)
            if y >= 0 and y < max_y and x >= 0 and x <= max_x:
                box_centers.append((x, y))
        return box_centers


    def _is_line_more_horizontal_please(self, line:'Line') -> bool:
        return line.theta >= pi/4 and line.theta <= 3*pi/4


    def _get_white_pixels_per_box_please(self, box_centers: 'list[tuple[int,int]]', edges) -> 'list[int]':
        max_x = edges.shape[1]
        max_y = edges.shape[0]
        pixels_per_box = []
        half_box_size = int(self._BOX_SIZE / 2)
        for (x, y) in box_centers:
            box = edges[y-half_box_size:y+half_box_size, x-half_box_size:x+half_box_size]
            pixels_per_box.append(np.count_nonzero(box == 255))
        return pixels_per_box


    def _get_tape_markers_please(self, white_pixels_per_box: 'list[int]') -> 'list[bool]':
        return [pixel_count > self._PIXELS_THRESHOLD for pixel_count in white_pixels_per_box]


    def _get_filtered_markers_please(self, tape_markers: 'list[bool]') -> 'list[bool]':
        filtered_markers = self._fill_gaps(tape_markers)
        filtered_markers = self._filter_small_segments(filtered_markers)
        return filtered_markers


    # TODO: probably don't need to fill up so aggressively, should rewrite
    def _fill_gaps(self, tape_markers: 'list[bool]') -> 'list[bool]':
        look_forward_amount = self._MIN_LINE_SEGMENT_HOLE_SIZE - 1
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
                elif current_segment_size + markers_forward + 1 >= self._MIN_LINE_SEGMENT_HOLE_SIZE:
                    gap_filled_markers[i : end_index + 1] = [True] * (end_index - i + 1)
                    current_segment_size += end_index - i
                    i = end_index - 1 # -1 because incrementing is the first step of the loop
        return gap_filled_markers


    def _filter_small_segments(self, gap_filled_markers: 'list[bool]') -> 'list[bool]':
        filtered_markers = gap_filled_markers.copy()
        i = 0
        while i < len(gap_filled_markers) - 1:
            start, end = self._get_next_segments_indices(gap_filled_markers, i)
            self._filter_segment_if_too_small(filtered_markers, start, end)
            i = i+1 if end is None else end
        return filtered_markers


    def _get_next_segments_indices(self, markers: 'list[bool]', start_from: int) -> 'tuple[int, int]':
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


    def _filter_segment_if_too_small(self, markers: 'list[bool]', segment_start: int, segment_end: int) -> 'list[bool]':
        if segment_start != None and segment_end - segment_start < self._MIN_LINE_SEGMENT_SIZE:
            markers[segment_start : segment_end + 1] = [False] * (segment_end - segment_start + 1)


    def _get_line_segments_please(self, markers: 'list[bool]', centers: 'list[tuple[int, int]]') -> 'list[LineSegment]':
        line_segments = []
        search_from = 0
        while search_from is not None:
            start, end = self._get_next_segments_indices(markers, search_from)
            if start is not None:
                start_x, start_y = centers[start]
                end_x, end_y = centers[end]
                line_segments.append(LineSegment((start_x, start_y), (end_x, end_y)))
            search_from = None if end is None else end + 1
        return line_segments


    def _get_tape_paths_and_lines(self, center_lines: 'list[Line]', tape_boundaries: 'dict[Line, list[LineSegment]]', frame) -> 'dict[LineSegment, Line]':
        tape_segments = [x for l in list(tape_boundaries.values()) for x in l]
        tape_paths_and_lines = {}
        if len(center_lines) == 1:
            frame_intersection_points = _get_line_frame_intersection_points(center_lines[0], frame)
            frame_intersection_points.sort(key= lambda point: point[1], reverse=True)
            bottom_point = frame_intersection_points[0]
            top_point = frame_intersection_points[1]
            path = LineSegment(bottom_point, top_point)
            tape_paths_and_lines = {path: center_lines[0]}
        elif len(center_lines) == 2:
            intersection_point = _get_intersection_point(center_lines[0], center_lines[1])
            center_line_segments = self._segment_center_lines(center_lines, intersection_point, frame)
            tape_paths = self._get_valid_center_line_segments(center_line_segments, tape_segments)
            tape_paths_and_lines = tape_paths
        return tape_paths_and_lines


    def _segment_center_lines(self, center_lines: 'list[Line]', intersection_point: 'tuple[int, int]', frame) -> 'dict[LineSegment, Line]':
        center_line_segments = {}
        for center_line in center_lines:
            frame_intersection_points = _get_line_frame_intersection_points(center_line, frame)
            for frame_intersection_point in frame_intersection_points:
                line_segment = LineSegment(intersection_point, frame_intersection_point)
                center_line_segments[line_segment] = center_line
        return center_line_segments


    def _get_valid_center_line_segments(self, center_line_segments: 'dict[LineSegment, Line]', tape_segments: 'list[LineSegment]') -> 'dict[LineSegment, Line]':
        valid_center_line_segments = {}
        for center_line_segment in list(center_line_segments.keys()):
            valid = True
            for tape_segment in tape_segments:
                if self._are_segments_intersecting(center_line_segment, tape_segment):
                    valid = False
            if valid:
                valid_center_line_segments[center_line_segment] = center_line_segments[center_line_segment]
        return valid_center_line_segments


    def _are_segments_intersecting(self, segment_one: 'LineSegment', segment_two: 'LineSegment') -> bool:
        A, B = segment_one.start_point, segment_one.end_point
        C, D = segment_two.start_point, segment_two.end_point
        return self._intersect(A, B, C, D)


    # https://stackoverflow.com/a/9997374
    def _ccw(self, A,B,C) -> bool:
        Ax, Ay = A
        Bx, By = B
        Cx, Cy = C
        return (Cy-Ay) * (Bx-Ax) > (By-Ay) * (Cx-Ax)


    # Return true if line segments AB and CD intersect
    def _intersect(self, A,B,C,D) -> bool:
        return self._ccw(A,C,D) != self._ccw(B,C,D) and self._ccw(A,B,C) !=self. _ccw(A,B,D)
    # https://stackoverflow.com/a/9997374


    def _get_median_line(self, lines: 'list[Line]') -> 'Line':
        has_to_convert = self._max_theta_diff(lines) > 2*Line._theta_diff_threshold
        rhos = []
        thetas = []
        for line in lines:
            rho = line.rho
            theta = line.theta
            if(has_to_convert and theta > pi - Line._theta_diff_threshold):
                line = self._convert_to_comparable_form(line)
                rho, theta = line.rho, line.theta
            rhos.append(rho)
            thetas.append(theta)
        median_rho = median(rhos)
        median_theta = median(thetas)
        return self._convert_to_conventional_form(Line(median_rho, median_theta))

    def _max_theta_diff(self, lines: 'list[Line]') -> float:
        min_theta = lines[0].theta
        max_diff = 0
        for line in lines:
            if (abs(line.theta - min_theta) > max_diff):
                max_diff = abs(line.theta - min_theta)
            if (line.theta < min_theta):
                min_theta = line.theta
        return max_diff

    def _get_centers_of_parallel_line_pairs(self, lines: 'list[Line]') -> 'list[Line]':
        if lines is None:
            return []
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
                center_lines.append(self._get_center_line(same_angle_lines[0], same_angle_lines[1]))

        return center_lines


    def _get_center_line(self, line_one: 'Line', line_two: 'Line') -> 'Line':
        if(abs(line_one.theta - line_two.theta) > Line._theta_diff_threshold):
            if line_one.theta > line_two.theta:
                line_one = self._convert_to_comparable_form(line_one)
            else:
                line_two = self._convert_to_comparable_form(line_two)

        rho_one, theta_one = line_one.rho, line_one.theta
        rho_two, theta_two = line_two.rho, line_two.theta

        mean_rho = (rho_one + rho_two) / 2
        mean_theta = (theta_one + theta_two) / 2
        center_line = Line(mean_rho, mean_theta)
        center_line = self._convert_to_conventional_form(center_line)

        return center_line


    def _convert_to_comparable_form(self, line: 'Line') -> 'Line':
        rho, theta = line.rho, line.theta
        # if(rho < 0):
        theta -= pi
        rho *= -1
        return Line(rho, theta)


    def _convert_to_conventional_form(self, line: 'Line') -> 'Line':
        rho, theta = line.rho, line.theta
        if theta < 0:
            theta += pi
            rho *= -1
        return Line(rho, theta)



# HELPER FUNCTIONS

def _get_line_frame_intersection_points(line: 'Line', frame) -> 'list[tuple[int, int]]':
        max_x = int(frame.shape[1] - 1)
        max_y = int(frame.shape[0] - 1)
        rho, theta = line.rho, line.theta
        x_intercept = int(rho*cos(theta) - rho*sin(theta)/tan(theta - pi/2))
        y_intercept = int(rho*sin(theta) - rho*cos(theta)*tan(theta - pi/2))
        possible_frame_intersection_points = [
            (0, y_intercept), # point is somewhere on the left side of the frame
            (max_x, int(tan(theta - pi/2)*max_x + y_intercept)), # point is somewhere on the right side of the frame
            (x_intercept, 0), # point is somewhere on the top of the frame
            (int(1/tan(theta - pi/2)*max_y + x_intercept), max_y) # point is somwhere on the bottom of the frame
        ]
        possible_frame_intersection_points = _filter_out_of_frame(possible_frame_intersection_points, max_x, max_y)
        frame_intersection_points = _filter_same_points(possible_frame_intersection_points)[0:2]
        return frame_intersection_points


def _filter_out_of_frame(possible_frame_intersection_points: 'list[tuple[int, int]]', max_x, max_y) -> 'list[tuple[int, int]]':
        filtered_points = []
        for possible_point in possible_frame_intersection_points:
            if _is_within_frame(possible_point, max_x, max_y):
                filtered_points.append(possible_point)
        return filtered_points

def _filter_same_points(possible_frame_intersection_points: 'list[tuple[int, int]]') -> 'list[tuple[int, int]]':
    return list(set(possible_frame_intersection_points))

def _is_within_frame(point: 'tuple[int, int]', max_x, max_y) -> bool:
        x, y = point
        return x >= 0 and x <= max_x and y >= 0 and y <= max_y


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