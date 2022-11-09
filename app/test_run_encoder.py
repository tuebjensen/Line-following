import asyncio
import sys

async def run_encoder ():
    encoder_process = await asyncio.create_subprocess_exec(
        sys.executable, 'run_encoder', '0',
        stdout = asyncio.subprocess.PIPE,
        stderr = asyncio.subprocess.DEVNULL,
        stdin = asyncio.subprocess.DEVNULL
    )
    while True:
        try:
            line = await asyncio.wait_for(encoder_process.stdout.readline(), 1)
            print(line.decode('ascii').rstrip())
        except asyncio.TimeoutError:
            pass

asyncio.run(run_encoder())