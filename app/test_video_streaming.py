import cv2 as cv
from lib_calculate_direction import DirectionCalculator
from lib_image_processing import ImageProcessor
from lib_process_lines import LineProcessor
from test_line_processing import get_processed_frame
from lib_web_server import WebServer
import asyncio
camera = cv.VideoCapture(0)
video = WebServer()
image_processor = ImageProcessor()
line_processor = LineProcessor()
direction_calculator = DirectionCalculator(video)

async def main():
    while camera.isOpened():
        ret_read, original_frame = camera.read()
        original_frame, velocity_vector = get_processed_frame(original_frame, image_processor, line_processor, direction_calculator)   
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