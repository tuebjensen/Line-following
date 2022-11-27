from math import asin, cos, pi, sin, sqrt
from lib_process_lines import Line, LineSegment, _get_intersection_point
from lib_vector2d import Vector2D
from os import getpid

STATE_FOLLOWING_LINE = 0
STATE_I_SEE_INTERSECTION = 1
STATE_TURNING = 2
STATE_STOP = 3
STATE_TURN180 = 4
STATE_IM_LOST = 5


class DirectionCalculator:
    def __init__(self, path_plan=[], state_change_threshold=10, react_to_intersection_threshold=0.3):
        self._STATE_CHANGE_THRESHOLD = state_change_threshold
        self._REACT_TO_INTERSECTION_THRESHOLD = react_to_intersection_threshold

        self._last_incoming_state = STATE_STOP
        self._same_incoming_states_count = self._STATE_CHANGE_THRESHOLD
        self._stable_state = STATE_STOP
        self._last_target = None
        self._last_line = None
        self._turning_just_initiated = False
        self._path_plan = path_plan


    def set_new_path(self, path_plan):
        print('new path plan')
        print(f'Before: {self}')
        print(path_plan)
        self._path_plan = path_plan
        if len(path_plan) > 0:
            self._stable_state = STATE_TURN180
        print(f'After: {self}')


    def get_direction_vector(self, tape_paths: 'dict[LineSegment, Line]', frame) -> Vector2D:
        target_path, target_line = self._decide_target(frame, tape_paths)
        if(target_path is None):
            return Vector2D(0, 0)
        displacement_vector = self._get_displacement_vector_from_center(target_line, frame)
        line_direction_vector = target_path.get_direction_vector_please()
        direction_vector = self._get_direction_to_go(displacement_vector, line_direction_vector, frame)
        return direction_vector


    def _get_direction_to_go(self, displacement_vector: Vector2D, direction_vector: Vector2D, image_frame) -> Vector2D:
        distance_from_center = displacement_vector.get_length()
        #Avoid dividing by zero when displacement vector has length zero

        displacement_vector = displacement_vector.normalize()
        direction_vector = direction_vector.normalize()

        frame_width = image_frame.shape[1]
        frame_height = image_frame.shape[0]
        maximum_distance_from_center = sqrt((frame_width / 2) ** 2 + (frame_height / 2) ** 2)

        displacement_vector_weight = distance_from_center / maximum_distance_from_center
        direction_vector_weight = 1 - displacement_vector_weight

        velocity_vector = direction_vector_weight * direction_vector + 1.5 * displacement_vector_weight * displacement_vector
        velocity_vector.normalize()

        return velocity_vector


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


    def _decide_target(self, original_frame, tape_paths) -> 'tuple[LineSegment, Line]':
        self._update_state(original_frame, tape_paths)
        state = self._stable_state
        target_path = None
        target_line = None
        # TODO: clean up -> current_node should be in some different process
        current_node = None
        
        if state == STATE_FOLLOWING_LINE:
            target_path, target_line = self._decide_target_from_following(tape_paths)
        elif state == STATE_I_SEE_INTERSECTION:
            target_path, target_line = self._decide_target_from_seeing_intersection(tape_paths)
        elif state == STATE_TURNING:
            target_path, target_line, current_node = self._decide_target_from_turning(tape_paths)
        elif state == STATE_STOP:
            #some input has to go here if we wanna be able to get out of this state
            target_path, target_line = self._decide_target_from_stopped()
        elif state == STATE_TURN180:
            target_path, target_line = self._decide_target_from_turning_180(original_frame)
        elif state == STATE_IM_LOST:
            target_path, target_line = self._decide_target_from_lost()

        self._last_target = target_path
        self._last_line = target_line

        return target_path, target_line, current_node


    def _update_state(self, frame, tape_paths_and_lines):
        parallel_line_centers = list(set(tape_paths_and_lines.values()))
        count_paths = len(list(tape_paths_and_lines.keys()))
        current_state = self._stable_state
        next_state = None

        if current_state == STATE_FOLLOWING_LINE:
            next_state = self._get_next_state_from_following(count_paths, parallel_line_centers, frame)
        elif current_state == STATE_I_SEE_INTERSECTION:
            next_state = self._get_next_state_from_seeing_intersection(count_paths, parallel_line_centers, frame)
        elif current_state == STATE_TURNING:
            next_state = self._get_next_state_from_turning(count_paths)
        elif current_state == STATE_STOP:
            next_state = self._get_next_state_from_stopped()
        elif current_state == STATE_TURN180:
            next_state = self._get_next_state_from_turning_around(count_paths)
        elif current_state == STATE_IM_LOST:
            next_state = self._get_next_state_from_lost(count_paths)
        else:
            pass
            #print(current_state)
        
        self._stable_state = self._get_stable_state(next_state)

    
    def _get_next_state_from_following(self, path_count, parallel_line_centers, frame):
        next_state = None
        if path_count > 1:
            intersection_red = _get_intersection_point(parallel_line_centers[0], parallel_line_centers[1])
            if intersection_red[1] > frame.shape[0]*self._REACT_TO_INTERSECTION_THRESHOLD:
                next_state = STATE_TURNING
                self._turning_just_initiated = True
            else:
                next_state = STATE_I_SEE_INTERSECTION
        elif path_count == 1:
            next_state = STATE_FOLLOWING_LINE
        elif path_count == 0:
            next_state = STATE_IM_LOST
        return next_state

    def _get_next_state_from_seeing_intersection(self, path_count, parallel_line_centers, frame):
        next_state = None
        if path_count > 1:
            intersection_red = _get_intersection_point(parallel_line_centers[0], parallel_line_centers[1])
            if intersection_red[1] > frame.shape[0]*self._REACT_TO_INTERSECTION_THRESHOLD:
                next_state = STATE_TURNING
                self._turning_just_initiated = True
            else:
                next_state = STATE_I_SEE_INTERSECTION
        elif path_count == 1:
            next_state = STATE_FOLLOWING_LINE
        elif path_count == 0:
            next_state = STATE_IM_LOST
        return next_state


    def _get_next_state_from_turning(self, path_count):
        next_state = None
        if path_count > 1:
            next_state = STATE_TURNING
            self._turning_just_initiated = False
        elif path_count == 1:
            next_state = STATE_FOLLOWING_LINE
        elif path_count == 0:
            next_state = STATE_IM_LOST
        return next_state


    def _get_next_state_from_stopped(self):
        #some input has to go here if we wanna be able to get out of this state
        next_state = STATE_STOP
        return next_state


    def _get_next_state_from_turning_around(self, path_count):
        next_state = None
        if path_count > 1:
            next_state = STATE_TURN180
            print('Turned around and saw an intersection')
        elif path_count == 1:
            next_state = STATE_FOLLOWING_LINE
        elif path_count == 0:
            next_state = STATE_TURN180
        print(f'was turning around, saw {path_count} paths, next state is {next_state}')
        return next_state


    def _get_next_state_from_lost(self, path_count):
        next_state = None
        if(len(self._path_plan) > 0 and self._path_plan[0]['choose'] == ''):
            next_state = STATE_STOP
        else:
            if path_count > 1:
                next_state = STATE_I_SEE_INTERSECTION
            elif path_count == 1:
                next_state = STATE_FOLLOWING_LINE
            elif path_count == 0:
                next_state = STATE_IM_LOST
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


    def _decide_target_from_following(self, tape_paths_and_lines):
        target_path = None
        target_line = None
        paths = list(tape_paths_and_lines.keys())
        if(len(paths) == 1): # stable state
            target_path = paths[0]
            target_line = tape_paths_and_lines.get(target_path)
        if(len(paths) > 1): # transient state
            target_path = self._get_most_like('back', tape_paths_and_lines).flip()
            target_line = tape_paths_and_lines.get(target_path)
        if(len(paths) == 0): # transient state
            target_path = self._last_target
            target_line = self._last_line
        return target_path, target_line

    
    def _decide_target_from_seeing_intersection(self, tape_paths_and_lines):
        target_path = None
        target_line = None
        paths = list(tape_paths_and_lines.keys())
        if(len(paths) > 1): # stable state
            target_path = self._get_most_like('back', tape_paths_and_lines).flip()
            target_line = tape_paths_and_lines.get(target_path)
        if(len(paths) <= 1): # transient state
            target_path = self._last_target
            target_line = self._last_line
        return target_path, target_line


    def _decide_target_from_turning(self, tape_paths_and_lines):
        target_path = None
        target_line = None
        current_node = None
        paths = list(tape_paths_and_lines.keys())
        if(len(paths) > 1): # stable state
            if self._turning_just_initiated:
                if len(self._path_plan) != 0:
                    instruction = self._path_plan.pop(0)
                    target_path = self._get_most_like(instruction['choose'], tape_paths_and_lines)
                    target_line = tape_paths_and_lines.get(target_path)
                    current_node = instruction['nodeId']
            else:
                target_path = self._update_target(self._last_target, tape_paths_and_lines) if self._last_target is not None else None
                target_line = tape_paths_and_lines.get(target_path)
        if(len(paths) <= 1): # transient state
            target_path = self._last_target
            target_line = self._last_line
        return target_path, target_line, current_node


    def _decide_target_from_stopped(self):
        return None, None


    def _decide_target_from_turning_180(self, original_frame):
        frame_width = original_frame.shape[1]
        frame_height = original_frame.shape[0]
        center = (int(frame_width / 2), int(frame_height / 2))
        center_left = (0, int(frame_height / 2))
        center_to_left = LineSegment(center, center_left)
        horizontal_line = Line(frame_height / 2, pi / 2)
        return center_to_left, horizontal_line


    def _decide_target_from_lost(self):
        return None, None


    def _get_most_like(self, turning_direction: str, tape_paths_and_lines: 'dict[LineSegment, Line]') -> LineSegment:
        for path in list(tape_paths_and_lines.keys()):
            angle = path.get_direction_vector_please().get_angle()
            if ((turning_direction == 'right' and angle >= -pi/4 and angle <= pi/4)
                    or (turning_direction == 'left' and ((angle >= 3*pi/4) or (angle <= -3*pi/4)))
                    or (turning_direction == 'straight' and angle >= -3*pi/4 and angle <= -pi/4)
                    or (turning_direction == 'back' and angle >= pi/4 and angle <= 3*pi/4)):
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

    def __str__(self):
        return (f'process id: {getpid()}, ' + \
            f'object id: {id(self)}, ' + \
            # f'last target: {self._last_target}, ' + \
            # f'last line: {self._last_line}, ' + \
            f'stable state: {self._stable_state}, ' + \
            f'last incoming state: {self._last_incoming_state}, ' + \
            f'same incoming states count: {self._same_incoming_states_count}, ' + \
            # f'turning just initiated: {self._turning_just_initiated}, ' + \
            f'path plan: {self._get_path_simplified_string()}')

    def _get_path_simplified_string(self):
        return [element.get('choose') for element in self._path_plan]

    def copy(self, other):
        self._last_target = other._last_target
        self._last_line = other._last_line
        self._stable_state = other._stable_state
        self._last_incoming_state = other._last_incoming_state
        self._same_incoming_states_count = other._same_incoming_states_count
        self._turning_just_initiated = other._turning_just_initiated
        self._path_plan = other._path_plan