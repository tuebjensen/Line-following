import cv2 as cv
import numpy as np

class ImageProcessor:
    def __init__(self, blur=10, block_size=5, c=3, threshold=65):
        self._BLUR = blur
        self._BLOCK_SIZE = block_size
        self._C = c
        self._THRESHOLD = threshold

    def get_edges_and_houghlines(self, camera_frame):
        processed_frame = self._process_frame(camera_frame)
        edges, lines = self._find_edges_and_houghlines(processed_frame)
        return edges, lines

    def _process_frame(self, camera_frame):
        processed_frame = cv.cvtColor(camera_frame, cv.COLOR_BGR2GRAY)
        processed_frame = cv.medianBlur(processed_frame, 2*self._BLUR+1)
        processed_frame = cv.adaptiveThreshold(
            processed_frame,
            255,
            cv.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv.THRESH_BINARY,
            2*(self._BLOCK_SIZE+1)+1,
            self._C)

    def _find_edges_and_houghlines(self, processed_frame):
        edges = cv.Canny(processed_frame, 50, 150, apertureSize = 3)
        houghlines = cv.HoughLines(edges, 1, np.pi/180, self._THRESHOLD)
        return edges, houghlines

    