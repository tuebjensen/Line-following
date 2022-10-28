from motor import Motor
import asyncio

class Car:
    def __init__(self, 
                motor_left_speed_pin: int, 
                motor_left_direction_pin: int, 
                motor_right_speed_pin: int,
                motor_right_direction_pin: int
                ):
        self._motor_left = Motor(motor_left_speed_pin, motor_left_direction_pin)
        self._motor_right = Motor(motor_right_speed_pin, motor_right_direction_pin)

    def set_velocity(self, direction_vector: tuple[float, float]):
        x, y = direction_vector
        epsilon = 0.1
        if x < -epsilon:
            self._motor_left.set_velocity(-1)
            self._motor_right.set_velocity(-1)
        elif x > epsilon or y < 0:
            self._motor_left.set_velocity(1)
            self._motor_right.set_velocity(1)
        else:
            self._motor_left.set_velocity(1)
            self._motor_right.set_velocity(-1)

    
    async def start_running(self):
        await asyncio.gather(
            self._motor_left.start_running(), 
            self._motor_right.start_running()
        )