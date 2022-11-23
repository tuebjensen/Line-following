import asyncio
from lib_motor import Motor
from math import atan2, pi

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
        # speed_factor = 1 - atan2(y, abs(x)) / (pi / 2) # TODO: Revise: y<0 means speed_factor > 1
        # epsilon = 0.1
        # if (x, y) == (0, 0):
        #     self._motor_left.set_speed(0)
        #     self._motor_right.set_speed(0)
        # #Turn left
        # elif x < -epsilon: 
        #     self._motor_left.set_speed(self._speed * speed_factor)
        #     self._motor_right.set_speed(self._speed * speed_factor)
        #     self._motor_left.set_forwards(False)
        #     self._motor_right.set_forwards(True)
        # #Turn right
        # elif x > epsilon or y < 0:
        #     self._motor_left.set_speed(self._speed * speed_factor)
        #     self._motor_right.set_speed(self._speed * speed_factor)
        #     self._motor_left.set_forwards(True)
        #     self._motor_right.set_forwards(False)
        # #Go straight
        # else:
        #     self._motor_left.set_speed(self._speed)
        #     self._motor_right.set_speed(self._speed)
        #     self._motor_left.set_forwards(True)
        #     self._motor_right.set_forwards(True)
        left_motor_intensity = y + x
        right_motor_intensity = y - x
        print(f'left_motor_intensity={left_motor_intensity}')
        print(f'right_motor_intensity={right_motor_intensity}')
        print(f'abs(self._speed * left_motor_intensity)={abs(self._speed * left_motor_intensity)}')
        print(f'abs(self._speed * right_motor_intensity)={abs(self._speed * right_motor_intensity)}')
        print(f'left_motor_intensity >= 0 = {left_motor_intensity >= 0}')
        print(f'right_motor_intensity >= 0 = {right_motor_intensity >= 0}')    
        self._motor_left.set_speed(abs(self._speed * left_motor_intensity))
        self._motor_left.set_forwards(left_motor_intensity >= 0)
        self._motor_right.set_speed(abs(self._speed * right_motor_intensity))
        self._motor_right.set_forwards(right_motor_intensity >= 0)

    
    async def start_running(self):
        await asyncio.gather(
            self._motor_left.start_running(), 
            self._motor_right.start_running()
        )