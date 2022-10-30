from motor import Motor
import asyncio

motor1 = Motor(speed_pin=32, direction_pin=36, encoder_interrupt_pin=11)
motor2 = Motor(speed_pin=33, direction_pin=31, encoder_interrupt_pin=37)

async def start():
    await asyncio.gather(
        motor1.start_running(),
        motor2.start_running()
    )

asyncio.run()