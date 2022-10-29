from math import asin, cos, pi, sin, sqrt
from process_lines import Line


class Vector2D:
    def __init__(self, x: float, y: float) -> 'Vector2D':
        self.x = x
        self.y = y
    
    def get_length(self) -> float:
        return sqrt(self.x ** 2 + self.y ** 2)

    def __add__(self, other):
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        if isinstance(scalar, int) or isinstance(scalar, float):
            return Vector2D(self.x * scalar, self.y * scalar)
        raise NotImplementedError('Can only multiply vector by a scalar')

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def __neg__(self) -> 'Vector2D':
        return Vector2D(-self.x, -self.y)

    def __truediv__(self, scalar) -> 'Vector2D':
        if isinstance(scalar, int) or isinstance(scalar, float):
            return Vector2D(self.x / scalar, self.y / scalar)
        raise NotImplementedError('Can only divide vector by a scalar')

    def dot(self, other: 'Vector2D') -> float:
        return self.x * other.x + self.y + other.y

    def normalize(self) -> 'Vector2D':
        return self / self.get_length()


def get_direction_to_go(line: Line, image_frame) -> Vector2D:
    direction_vector = _get_direction_vector_of_line(line).normalize()
    displacement_vector = _get_displacement_vector_from_center(line, image_frame)
    distance_from_center = displacement_vector.get_length()
    displacement_vector = displacement_vector.normalize()

    frame_width = image_frame.shape[1]
    frame_height = image_frame.shape[0]
    maximum_distance_from_center = sqrt((frame_width / 2) ** 2 + (frame_height / 2) ** 2)

    displacement_vector_weight = distance_from_center / maximum_distance_from_center
    direction_vector_weight = 1 - displacement_vector_weight

    return direction_vector_weight * direction_vector + displacement_vector_weight * displacement_vector

def _get_direction_vector_of_line(line: Line) -> Vector2D:
    theta = line.theta
    adjusted_theta = -1 * theta
    perpendicular_angle = adjusted_theta + pi / 2
    x = cos(perpendicular_angle)
    y = sin(perpendicular_angle)
    return Vector2D(x, y)

def _get_displacement_vector_from_center(line: Line, frame) -> Vector2D:
    rho, theta = line.rho, line.theta

    frame_width = frame.shape[1]
    frame_height = frame.shape[0]
    center = Vector2D(frame_width / 2, -1 * frame_height / 2)
    max_distance = center.get_length()

    displacement_angle = pi - theta
    gamma = asin((frame_height / 2) / max_distance)
    displacement_length = (max_distance - (rho / sin(pi / 2 - theta + gamma))) * sin(pi / 2 - theta + gamma)

    return Vector2D(displacement_length * cos(displacement_angle), displacement_length * sin(displacement_angle))
