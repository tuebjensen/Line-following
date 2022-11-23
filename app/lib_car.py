import asyncio
from lib_motor import Motor
from math import atan2, pi, sqrt

class Car:
    def __init__(self, motor_left: Motor, motor_right: Motor, speed = None):
        self._motor_left = motor_left
        self._motor_right = motor_right
        self._speed = speed
        if speed is None:
            speed = (self._motor_left + self._motor_right) / 2
        self._motor_left.set_speed(speed)
        self._motor_right.set_speed(speed)

    def set_velocity(self, direction_vector: tuple[float, float]):
        if direction_vector is None:
            return
        x, y = direction_vector
        left_motor_intensity = (y + x) / sqrt(2)
        right_motor_intensity = (y - x) / sqrt(2)  
        self._motor_left.set_speed(abs(self._speed * left_motor_intensity))
        self._motor_left.set_forwards(left_motor_intensity >= 0)
        self._motor_right.set_speed(abs(self._speed * right_motor_intensity))
        self._motor_right.set_forwards(right_motor_intensity >= 0)

    
    async def start_running(self):
        await asyncio.gather(
            self._motor_left.start_running(), 
            self._motor_right.start_running()
        )