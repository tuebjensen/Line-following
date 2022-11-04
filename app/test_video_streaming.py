import cv2 as cv
from lib_video_streaming import VideoStreaming
import asyncio
camera = cv.VideoCapture(0)
video = VideoStreaming()

video.start_running()

'''async def start():
    while camera.isOpened():
        ret, original_frame = camera.read()    
        ret, buffer = cv.imencode('.jpg', original_frame)
        frame = buffer.tobytes()
        video.set_frame_encoded(frame)
        await asyncio.sleep(0.1)
    camera.release()

asyncio.run(start())'''