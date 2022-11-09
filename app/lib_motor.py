from time import time
import RPi.GPIO as GPIO
from simple_pid import PID
import asyncio
import sys
import signal
class Motor:
    def __init__(
        self,
        speed_pin: int,
        direction_pin: int,
        encoder_interrupt_pin: int,
        speed: int = 20,
        forwards: bool = True
    ):
        self._speed_pin = speed_pin
        self._direction_pin = direction_pin
        self._encoder_interrupt_pin = encoder_interrupt_pin
        self._encoder_interrupt_count = 0
        self._speed = speed
        self._forwards = forwards
        self._running = False
        self._pid = None

    def _encoder_callback(self, arg):
        self._encoder_interrupt_count += 1

    def set_speed(self, speed):
        if self._pid is not None:
            self._pid.setpoint = speed
        self._speed = speed

    def set_forwards(self, forwards):
        self._forwards = forwards

    async def start_running(self):
        # make sure we don't run it twice
        if self._running:
            return
        self._running = True

        async def do_pid():
            try:
                # control the speed of the motor
                while True:
                    #print("PID", time())
                    GPIO.output(self._direction_pin, self._forwards)
                    output = self._pid(self._encoder_interrupt_count)
                    self._encoder_interrupt_count = 0
                    self._speed_pwm.ChangeDutyCycle(output if not self._forwards else 100 - output)
                    await asyncio.sleep(0.1)
            except RuntimeError:
                pass
        
        async def do_encoder_process():
            while True:
                output = await encoder_process.stdout.readline()
                outputStr = output.decode('ascii').rstrip()
                if (outputStr.isdigit() and len(outputStr) > 0):
                    self._encoder_interrupt_count = int(outputStr)
                    print(self._encoder_interrupt_count)
                await asyncio.sleep(0)

        def signal_handler(sig, frame):
            encoder_process.kill()
        # setup pins
        GPIO.setup(self._speed_pin, GPIO.OUT)
        GPIO.setup(self._direction_pin, GPIO.OUT)

        encoder_process = await asyncio.create_subprocess_exec(
            sys.executable, 'run_encoder.py', str(self._encoder_interrupt_pin),
            stdout = asyncio.subprocess.PIPE,
            stderr = asyncio.subprocess.STDOUT,
            stdin = asyncio.subprocess.DEVNULL
        )
        signal.signal(signal.SIGINT, signal_handler)
        GPIO.output(self._direction_pin, self._forwards)

        # setup PID for the encoder(=input) + dutycycle(=output)        
        pid = PID(0.25, 1, 0.025, setpoint=self._speed)
        pid.sample_time = 0.1
        pid.output_limits = (0, 100)
        pid.auto_mode = True
        self._pid = pid

        self._speed_pwm = GPIO.PWM(self._speed_pin, 50) # 50 Hz

        #GPIO.add_event_detect(self._encoder_interrupt_pin, GPIO.FALLING, callback=self._encoder_callback)
        # (lambda arg: Motor._encoder_callback(self, arg)

        # start with a small duty cycle
        self._speed_pwm.start(5 if not self._forwards else 95)
        await asyncio.gather(do_pid(), do_encoder_process())