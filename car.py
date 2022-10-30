from motor import Motor
import asyncio

class Car:
    def __init__(self, 
                motor_left_speed_pin: int, 
                motor_left_direction_pin: int, 
                motor_left_encoder_pin: int,
                motor_right_speed_pin: int,
                motor_right_direction_pin: int,
                motor_right_encoder_pin: int,
                speed: int = 20
        ):
        self._motor_left = Motor(motor_left_speed_pin, motor_left_direction_pin, motor_left_encoder_pin, speed)
        self._motor_right = Motor(motor_right_speed_pin, motor_right_direction_pin, motor_right_encoder_pin, speed)
        self._speed = speed

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