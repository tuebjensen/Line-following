import asyncio
import sys
import os

async def run_encoder ():
    encoder_process = await asyncio.create_subprocess_exec(
        os.path.join(os.path.dirname(__file__), 'run_encoder'), '0',
        stdout = asyncio.subprocess.PIPE,
        stderr = asyncio.subprocess.DEVNULL,
        stdin = asyncio.subprocess.DEVNULL
    )
    while True:
        try:
            line = await asyncio.wait_for(encoder_process.stdout.readline(), 1)
            print(line)
        except asyncio.TimeoutError:
            pass

asyncio.run(run_encoder())