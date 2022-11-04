from math import asin, cos, pi, sin, sqrt
from lib_process_lines import Line
from lib_vector2d import Vector2D

def get_direction_to_go(line: Line, image_frame) -> Vector2D:
    direction_vector = get_direction_vector_of_line(line).normalize()
    displacement_vector = get_displacement_vector_from_center(line, image_frame)
    distance_from_center = len(displacement_vector)
    displacement_vector = displacement_vector.normalize()

    frame_width = image_frame.shape[1]
    frame_height = image_frame.shape[0]
    maximum_distance_from_center = sqrt((frame_width / 2) ** 2 + (frame_height / 2) ** 2)

    displacement_vector_weight = distance_from_center / maximum_distance_from_center
    direction_vector_weight = 1 - displacement_vector_weight

    return direction_vector_weight * direction_vector + displacement_vector_weight * displacement_vector

def get_direction_vector_of_line(line: Line) -> Vector2D:
    theta = line.theta
    adjusted_theta = -1 * theta
    perpendicular_angle = adjusted_theta + pi / 2
    x = cos(perpendicular_angle)
    y = sin(perpendicular_angle)
    return Vector2D(x, y)

def get_displacement_vector_from_center(line: Line, frame) -> Vector2D:
    rho, theta = line.rho, line.theta

    frame_width = frame.shape[1]
    frame_height = frame.shape[0]
    center = Vector2D(frame_width / 2, -1 * frame_height / 2)
    max_distance = len(center)

    displacement_angle = pi - theta
    gamma = asin((frame_height / 2) / max_distance)
    displacement_length = (max_distance - (rho / sin(pi / 2 - theta + gamma))) * sin(pi / 2 - theta + gamma)

    return Vector2D(displacement_length * cos(displacement_angle), displacement_length * sin(displacement_angle))
