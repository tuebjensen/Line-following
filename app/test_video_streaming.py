import cv2 as cv
from test_line_processing import get_processed_frame
from lib_web_server import WebServer
import asyncio
camera = cv.VideoCapture(0)
video = WebServer()


async def main():
    while camera.isOpened():
        ret_read, original_frame = camera.read()
        original_frame, velocity_vector = get_processed_frame(original_frame)   
        ret, buffer = cv.imencode('.jpg', original_frame)
        frame = buffer.tobytes()
        video.set_frame_encoded(frame)
        await asyncio.sleep(0.1)
    camera.release()

def path_callback(path):
    pass
    # print(path)

def parse_path(path):
    pass
async def start():
    await asyncio.gather(video.start_running('0.0.0.0', 5000, path_callback), main())
asyncio.run(start())