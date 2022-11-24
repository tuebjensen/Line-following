from math import asin, cos, pi, sin, sqrt
import numpy as np
from lib_process_lines import Line, LineSegment, _get_intersection_point
from lib_vector2d import Vector2D


STATE_FOLLOWING_LINE = 0
STATE_I_SEE_INTERSECTION = 1
STATE_TURNING = 2
STATE_STOP = 3
STATE_TURN180 = 4
STATE_IM_LOST = 5


class DirectionCalculator:
    def __init__(self, initial_orientation, path_plan=['R', 'R', 'R', 'R'], state_change_threshold=10, react_to_intersection_threshold=0.3):
        self._orientation = initial_orientation
        self._path_plan = path_plan
        self._STATE_CHANGE_THRESHOLD = state_change_threshold
        self._REACT_TO_INTERSECTION_THRESHOLD = react_to_intersection_threshold

        self._last_incoming_state = STATE_FOLLOWING_LINE
        self._same_incoming_states_count = self._STATE_CHANGE_THRESHOLD
        self._stable_state = STATE_FOLLOWING_LINE
        self._last_target = None
        self._last_line = None
        self._turning_just_initiated = False
        self._close_my_eyes = False

    def get_direction_vector(self, tape_paths: 'dict[LineSegment, Line]', frame) -> Vector2D:
        target_path = self._decide_target(tape_paths)
        target_line = tape_paths.get(target_path)
        displacement_vector = self._get_displacement_vector_from_center(target_line, frame)
        line_direction_vector = target_path.get_direction_vector_please()
        direction_vector = self._get_direction_to_go(displacement_vector, line_direction_vector, frame)
        return direction_vector


    def _get_direction_to_go(self, displacement_vector: Vector2D, direction_vector: Vector2D, image_frame) -> Vector2D:
        distance_from_center = displacement_vector.get_length()
        displacement_vector = displacement_vector.normalize()
        direction_vector = direction_vector.normalize()

        frame_width = image_frame.shape[1]
        frame_height = image_frame.shape[0]
        maximum_distance_from_center = sqrt((frame_width / 2) ** 2 + (frame_height / 2) ** 2)

        displacement_vector_weight = distance_from_center / maximum_distance_from_center
        direction_vector_weight = 1 - displacement_vector_weight

        return direction_vector_weight * direction_vector + displacement_vector_weight * displacement_vector

    def _get_direction_vector_of_line(self, line: Line) -> Vector2D:
        theta = line.theta
        adjusted_theta = -1 * theta
        perpendicular_angle = adjusted_theta + pi / 2
        x = cos(perpendicular_angle)
        y = sin(perpendicular_angle)
        return Vector2D(x, y)

    def _get_displacement_vector_from_center(self, line: Line, frame) -> Vector2D:
        rho, theta = line.rho, line.theta

        frame_width = frame.shape[1]
        frame_height = frame.shape[0]
        center = Vector2D(frame_width / 2, -1 * frame_height / 2)
        max_distance = center.get_length()

        displacement_angle = pi - theta
        gamma = asin((frame_height / 2) / max_distance)
        displacement_length = (max_distance - (rho / sin(pi / 2 - theta + gamma))) * sin(pi / 2 - theta + gamma)

        x_coord = displacement_length * cos(displacement_angle)
        y_coord = -1 * displacement_length * sin(displacement_angle) # have to multiply by -1 because of difference in reference frame

        return Vector2D(x_coord, y_coord)

    def _decide_target(self, original_frame, tape_paths) -> LineSegment:
        parallel_line_centers = list(tape_paths.values())
        state = self._get_next_state(self._stable_state, original_frame, parallel_line_centers, tape_paths)
        self._stable_state = state
        target = None
        line = None
        paths = list(tape_paths.keys())
        if state == STATE_FOLLOWING_LINE:
            if(len(paths) == 1): # stable state
                target = paths[0]
                line = tape_paths.get(target)
            if(len(paths) > 1): # transient state
                target = self._get_most_like('B', tape_paths).flip()
                line = tape_paths.get(target)
            if(len(paths) == 0): # transient state
                target = self._last_target
                line = self._last_line
        elif state == STATE_I_SEE_INTERSECTION:
            if(len(paths) > 1): # stable state
                target = self._get_most_like('B', tape_paths).flip()
                line = tape_paths.get(target)
            if(len(paths) <= 1): # transient state
                target = self._last_target
                line = self._last_line
        elif state == STATE_TURNING:
            if(len(paths) > 1): # stable state
                if self._turning_just_initiated: 
                    if len(self._path_plan) != 0:
                        turning_dir = self._path_plan.pop(0)
                        target = self._get_most_like(turning_dir, tape_paths)
                        line = tape_paths.get(target)
                else:
                    target = self._update_target(self._last_target, tape_paths) if self._last_target is not None else None
                    line = tape_paths.get(target)
            if(len(paths) <= 1): # transient state
                target = self._last_target
                line = self._last_line
        elif state == STATE_STOP:
            #some input has to go here if we wanna be able to get out of this state
            pass
        elif state == STATE_TURN180:
            pass 
        elif state == STATE_IM_LOST:
            target = None
            line = None
        self._last_target = target
        self._last_line = line
        return target, line


    def _get_next_state(self, current_state, frame, parallel_line_centers, tape_paths_and_lines):
        count_paths = len(list(tape_paths_and_lines.keys()))
        next_state = None
        if current_state == STATE_FOLLOWING_LINE:
            if count_paths > 1:
                intersection_red = _get_intersection_point(parallel_line_centers[0], parallel_line_centers[1])
                if intersection_red[1] > frame.shape[0]*self._REACT_TO_INTERSECTION_THRESHOLD:
                    next_state = STATE_TURNING
                    self._turning_just_initiated = True
                else:
                    next_state = STATE_I_SEE_INTERSECTION
            elif count_paths == 1:
                next_state = STATE_FOLLOWING_LINE
            elif count_paths == 0:
                next_state = STATE_IM_LOST
        elif current_state == STATE_I_SEE_INTERSECTION:
            if count_paths > 1:
                intersection_red = _get_intersection_point(parallel_line_centers[0], parallel_line_centers[1])
                if intersection_red[1] > frame.shape[0]*self._REACT_TO_INTERSECTION_THRESHOLD:
                    next_state = STATE_TURNING
                    self._turning_just_initiated = True
                else:
                    next_state = STATE_I_SEE_INTERSECTION
            elif count_paths == 1:
                next_state = STATE_FOLLOWING_LINE
            elif count_paths == 0:
                next_state = STATE_IM_LOST
        elif current_state == STATE_TURNING:
            if count_paths > 1:
                next_state = STATE_TURNING
                self._turning_just_initiated = False
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
                if self._close_my_eyes is True:
                    next_state = STATE_TURN180
                else:
                    next_state = STATE_FOLLOWING_LINE
            elif count_paths == 0:
                self._close_my_eyes = False
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

        next_state = self._get_stable_state(next_state)
        return next_state


    def _get_stable_state(self, incoming_state):
        if incoming_state != self._stable_state:
            if incoming_state == self._last_incoming_state:
                self._same_incoming_states_count += 1
                if self._same_incoming_states_count >= self._STATE_CHANGE_THRESHOLD:
                    self._same_incoming_states_count = 1
                    return incoming_state
            else :
                self._same_incoming_states_count = 1
            
            self._last_incoming_state = incoming_state

        return self._stable_state


    def _get_most_like(self, turning_direction: str, tape_paths_and_lines: 'dict[LineSegment, Line]') -> LineSegment:
        for path in list(tape_paths_and_lines.keys()):
            angle = path.get_direction_vector_please().get_angle()
            if ((turning_direction == 'R' and angle >= -pi/4 and angle <= pi/4)
                    or (turning_direction == 'L' and ((angle >= 3*pi/4) or (angle <= -3*pi/4)))
                    or (turning_direction == 'S' and angle >= -3*pi/4 and angle <= -pi/4)
                    or (turning_direction == 'B' and angle >= pi/4 and angle <= 3*pi/4)):
                return path
        
        print('your map sucks')

    def _update_target(self, old_target: LineSegment, tape_paths_and_lines: 'dict[LineSegment, Line]') -> LineSegment:
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
