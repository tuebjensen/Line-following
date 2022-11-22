import cv2 as cv
import numpy as np


def nothing(x):
    pass

def process_frame(frame, blur, block_size, c):
    processed_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    processed_frame = cv.medianBlur(processed_frame, 2*blur+1)
    processed_frame = cv.adaptiveThreshold(processed_frame, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 2*(block_size+1)+1, c)
    return processed_frame

def find_edges_and_lines(frame, threshold):
    edges = cv.Canny(frame, 50, 150, apertureSize = 3)
    lines = cv.HoughLines(edges, 1, np.pi/180, threshold)
    return edges, lines
