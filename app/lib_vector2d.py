from math import sqrt

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