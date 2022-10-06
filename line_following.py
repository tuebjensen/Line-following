import cv2 as cv
import numpy as np
def nothing(x):
    pass
def process_frame(frame, blur, block_size, c):
    processed_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    processed_frame = cv.medianBlur(processed_frame, 2*blur+1)
    processed_frame = cv.adaptiveThreshold(processed_frame, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 2*(block_size+1)+1, c)
    return processed_frame

def find_edges_and_lines(frame):
    edges = cv.Canny(frame, 50, 150, apertureSize = 3)
    lines = cv.HoughLines(edges, 1, np.pi/180, 100)
    return edges, lines


def main():
    guard = True
    cap = cv.VideoCapture('flash test.mp4')
    img = np.zeros((25, 500, 3), np.uint8)
    cv.namedWindow('image')
    cv.createTrackbar('Blur', 'image', 5, 100, nothing)
    cv.createTrackbar('Block size', 'image', 5, 100, nothing)
    cv.createTrackbar('C', 'image', 5, 100, nothing)
    while cap.isOpened() and guard:
        ret, original_frame = cap.read()
        if not ret:
            print("Can't receive next frame")
            cap.set(cv.CAP_PROP_POS_FRAMES, 0)
            continue
        
        blur = cv.getTrackbarPos('Blur', 'image')
        block_size = cv.getTrackbarPos('Block size', 'image')
        c = cv.getTrackbarPos('C', 'image')
        processed_frame = process_frame(original_frame, blur, block_size, c)
        edges, lines = find_edges_and_lines(processed_frame)    
        if isinstance(lines, np.ndarray):
            cv.putText(original_frame, f'lines: {len(lines)}', (0,50), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv.LINE_AA)
            for line in lines:
                rho,theta = line[0]
                a = np.cos(theta)
                b = np.sin(theta)
                x0 = a*rho
                y0 = b*rho
                x1 = int(x0 + 1000*(-b))
                y1 = int(y0 + 1000*(a))
                x2 = int(x0 - 1000*(-b))
                y2 = int(y0 - 1000*(a))
                cv.line(original_frame, (x1,y1), (x2,y2), (255,0,0), 2)

        cv.imshow('original video', original_frame)
        cv.imshow('processed video', processed_frame)
        cv.imshow('edges', edges)
        cv.imshow('image', img)
        cv.moveWindow('processed video', 700, 208)
        cv.moveWindow('edges', 1200, 208)
        if cv.waitKey(10) == ord('q'):
            guard = False
    cap.release()
    cv.destroyAllWindows()


if __name__ == "__main__":
    main()