import asyncio
import sys

async def run_encoder ():
    encoder_process = await asyncio.create_subprocess_exec(
        sys.executable, 'run_encoder.py', '11',
        stdout = asyncio.subprocess.PIPE,
        stderr = asyncio.subprocess.DEVNULL,
        stdin=asyncio.subprocess.DEVNULL
    )
    while True:
        print('hello')
        try:
            async with asyncio.timeout(1):
                await encoder_process.stdout.readline()
        except TimeoutError:
            pass
        sys.stdout.write('hoy\n')
        print('hoy')

asyncio.run(run_encoder())