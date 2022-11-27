import cv2 as cv
from lib_calculate_direction import DirectionCalculator
from lib_image_processing import ImageProcessor
from lib_process_lines import LineProcessor
from test_line_processing import get_processed_frame
from lib_web_server import WebServer
import asyncio
camera = cv.VideoCapture(0)
video = WebServer()
image_processor = ImageProcessor(10, 5, 7, 85)
line_processor = LineProcessor()
direction_calculator = DirectionCalculator()


path_plan = []
unread_new_path = False

def write_path(path):
    global path_plan
    path_plan = path
    global unread_new_path
    unread_new_path = True

def read_path():
    global unread_new_path
    unread_new_path = False
    global path_plan
    return path_plan


async def main():
    global direction_calculator
    while camera.isOpened():
        ret_read, original_frame = camera.read()
        if(unread_new_path):
            path = read_path()
            direction_calculator.set_new_path(path)
        processed_frame_info = get_processed_frame(original_frame, image_processor, line_processor, direction_calculator)   
        direction_calculator.copy(processed_frame_info['direction_calculator'])
        processed_frame = processed_frame_info['frame']
        ret, buffer = cv.imencode('.jpg', processed_frame)
        frame = buffer.tobytes()
        video.set_frame_encoded(frame)
        await asyncio.sleep(0.1)
    camera.release()


def parse_path(path):
    pass


async def start():
    await asyncio.gather(video.start_running('0.0.0.0', 5000, write_path), main())
asyncio.run(start())