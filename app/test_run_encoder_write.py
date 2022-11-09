import asyncio
import sys

async def run_encoder ():
    encoder_process = await asyncio.create_subprocess_exec(
        sys.executable, 'run_encoder_write', '0',
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