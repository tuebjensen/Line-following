import asyncio
import sys

async def run_encoder ():
    encoder_process = await asyncio.create_subprocess_exec(
        sys.executable, 'run_encoder.py', '11',
        stdout = asyncio.subprocess.PIPE,
        stderr = asyncio.subprocess.STDOUT,
        stdin=asyncio.subprocess.DEVNULL
    )
    while True:
        print('hello')
        line = await asyncio.wait_for(encoder_process.stdout.readline(), 100)
        print('hoy')

asyncio.run(run_encoder())