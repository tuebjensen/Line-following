import asyncio
from lib_motor import Motor

class Car:
    def __init__(self, motor_left: Motor, motor_right: Motor, speed = None):
        self._motor_left = motor_left
        self._motor_right = motor_right
        if speed is None:
            speed = (self._motor_left + self._motor_right) / 2
        self._motor_left.set_speed(speed)
        self._motor_right.set_speed(speed)

    def set_velocity(self, direction_vector: tuple[float, float]):
        x, y = direction_vector
        epsilon = 0.1
        #Turn left
        if x < -epsilon:
            self._motor_left.set_forwards(False)
            self._motor_right.set_forwards(True)
        #Turn right
        elif x > epsilon or y < 0:
            self._motor_left.set_forwards(True)
            self._motor_right.set_forwards(False)
        #Go straight
        else:
            self._motor_left.set_forwards(True)
            self._motor_right.set_forwards(True)

    
    async def start_running(self):
        await asyncio.gather(
            self._motor_left.start_running(), 
            self._motor_right.start_running()
        )