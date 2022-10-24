from math import asin, atan2, cos, pi, sin, sqrt
import cv2 as cv
import numpy as np
import statistics

RHO_DIFFERENCE_THRESHOLD = 80
THETA_DIFFERENCE_THRESHOLD = 0.3

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

def merge_lines(lines):
    if lines is None:
        return lines
    # merge lines by making a dict with tuple for keys, holding both rho and theta values
    similar_lines = {}
    for line in lines:
        current_rho, current_theta = line[0]
        found_similar = False
        for group_leading_line, grouped_lines in similar_lines.items():
            group_leading_rho, group_leading_theta = group_leading_line
            # difference in distance is less than 15 pixels, and difference in angle is less than 0.1 radians ~ 5-10°
            if abs(group_leading_rho - current_rho) < RHO_DIFFERENCE_THRESHOLD and abs(group_leading_theta - current_theta) < THETA_DIFFERENCE_THRESHOLD :
                grouped_lines.append((current_rho, current_theta))
                found_similar = True
                break
        if not found_similar:
            similar_lines[(current_rho, current_theta)] = [(current_rho, current_theta)]

    merged_lines = []
    for group_leading_line, grouped_lines in similar_lines.items():
        grouped_rhos = []
        grouped_thetas = []
        for line in grouped_lines:
            rho, theta = line
            grouped_rhos.append(rho)
            grouped_thetas.append(theta)
        median_rho = statistics.median(grouped_rhos)
        median_theta = statistics.median(grouped_thetas)
        merged_lines.append((median_rho, median_theta))
    
    return merged_lines

def get_parallel_line_centers(merged_lines):
    if merged_lines is None:
        return merged_lines

    parallel_lines = {}
    for line in merged_lines:
        theta = line[1]
        found_similar = False
        for parallel_line_theta, same_theta_lines in parallel_lines.items():
            if abs(theta - parallel_line_theta) < 2*THETA_DIFFERENCE_THRESHOLD:
                same_theta_lines.append(line)
                found_similar = True
                break
        if not found_similar:
            parallel_lines[theta] = [line]
    
    line_centers = []
    for parallel_line_theta, same_theta_lines in parallel_lines.items():
        if(len(same_theta_lines) != 2):
            continue
        parallel_rhos = []
        parallel_thetas = []
        for line in same_theta_lines:
            parallel_rhos.append(line[0])
            parallel_thetas.append(line[1])
        center_rho = statistics.median(parallel_rhos)
        center_theta = statistics.median(parallel_thetas)
        line_centers.append((center_rho, center_theta))
    return line_centers

def get_direction_to_go(line, original_frame):
    direction_vector = normalize(get_direction_vector_of_line(line))
    displacement_vector = get_displacement_vector_from_center(line, original_frame)
    distance_from_center = get_length(displacement_vector)
    displacement_vector = normalize(displacement_vector)

    frame_width = original_frame.shape[1]
    frame_height = original_frame.shape[0]
    maximum_distance_from_center = sqrt((frame_width / 2) ** 2 + (frame_height / 2) ** 2)

    displacement_vector_weight = distance_from_center / maximum_distance_from_center
    direction_vector_weight = 1 - displacement_vector_weight

    return add(scale(direction_vector, direction_vector_weight), scale(displacement_vector, displacement_vector_weight))

def get_direction_vector_of_line(line):
    rho, theta = line
    adjusted_theta = -1 * theta
    perpendicular_angle = adjusted_theta + pi / 2
    x = np.cos(perpendicular_angle)
    y = np.sin(perpendicular_angle)
    return (x, y)

def get_displacement_vector_from_center(line, frame):
    rho, theta = line
    a = np.cos(theta)
    b = np.sin(theta)

    frame_width = frame.shape[1]
    frame_height = frame.shape[0]
    center_point = (frame_width / 2, -1 * frame_height / 2)

    max_distance = get_length(center_point)
    displacement_angle = pi - theta

    gamma = asin((frame_height / 2) / max_distance)
    displacement_length = (max_distance - (rho / sin(pi / 2 - theta + gamma))) * sin(pi / 2 - theta + gamma)

    displacement_vector = (displacement_length * cos(displacement_angle), displacement_length * sin(displacement_angle))

    return displacement_vector

def get_length(vector):
    return sqrt(vector[0] ** 2 + vector[1] ** 2)

def normalize(vector):
    vector_length = get_length(vector)
    return scale(vector, 1 / vector_length)

def scale(vector, factor):
    return (vector[0] * factor, vector[1] * factor)

def add(vector_1, vector_2):
    return (vector_1[0] + vector_2[0], vector_1[1] + vector_2[1])

def subtract(vector_1, vector_2):
    return (vector_1[0] - vector_2[0], vector_1[1] - vector_2[1])

def dot(vector_1, vector_2):
    return vector_1[0] * vector_2[0] + vector_1[1] + vector_2[1]

def display_all_lines(lines, original_frame):
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

def display_merged_parallel_lines(merged_lines, original_frame):
    for i in range(len(merged_lines)):
        line = merged_lines[i]
        cv.putText(original_frame, f'line: rho{line[0]}, theta: {line[1] * 180 / 3.1415}°', (50, 50+i*50), cv.FONT_HERSHEY_SIMPLEX, 1, (0,255-255/len(merged_lines)*i,0), 2, cv.LINE_AA)
        rho,theta = line
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a*rho
        y0 = b*rho
        x1 = int(x0 + 1000*(-b))
        y1 = int(y0 + 1000*(a))
        x2 = int(x0 - 1000*(-b))
        y2 = int(y0 - 1000*(a))
        cv.line(original_frame, (x1,y1), (x2,y2), (0,255-255/len(merged_lines)*i,0), 2)

def display_center_of_parallel_lines(parallel_line_centers, original_frame):
    for i in range(len(parallel_line_centers)):
        line = parallel_line_centers[i]
        cv.putText(original_frame, f'line: rho{line[0]}, theta: {line[1] * 180 / 3.1415 }°', (50, 50+len(parallel_line_centers)+i*50), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0, 255-255/len(parallel_line_centers)*i), 2, cv.LINE_AA)
        rho,theta = line
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a*rho
        y0 = b*rho
        x1 = int(x0 + 1000*(-b))
        y1 = int(y0 + 1000*(a))
        x2 = int(x0 - 1000*(-b))
        y2 = int(y0 - 1000*(a))
        cv.line(original_frame, (x1,y1), (x2,y2), (0,0, 255-255/len(parallel_line_centers)*i), 2)


def display_displacement_and_direction_vectors(parallel_line_centers, frame):
    if(not isinstance(parallel_line_centers, (list, tuple, np.ndarray))):
        return
    if(len(parallel_line_centers) < 1):
        return
    line = parallel_line_centers[0]
    displacement_vector = get_displacement_vector_from_center(line, frame)
    frame_width = frame.shape[1]
    frame_height = frame.shape[0]
    center_x = frame_width / 2
    center_y = frame_height / 2
    cv.line(frame, (int(center_x), int(center_y)), (int(displacement_vector[0]) + int(center_x), int(center_y) - int(displacement_vector[1])), (255,255,0), 2)
    direction_vector = scale(get_direction_vector_of_line(line), 200)
    cv.line(frame,
        (int(displacement_vector[0]) + int(center_x), int(center_y) - int(displacement_vector[1])),
        (int(displacement_vector[0]) + int(direction_vector[0]) + int(center_x), int(center_y) - int(direction_vector[1]) - int(displacement_vector[1])),
        (0,255,255),
        2
    )


# def display_direction_vector(parallel_line_centers, frame):
#     if(not isinstance(parallel_line_centers, (list, tuple, np.ndarray))):
#         return
#     if(len(parallel_line_centers) < 1):
#         return
#     line = parallel_line_centers[0]
#     frame_width = frame.shape[1]
#     frame_height = frame.shape[0]
#     center_x = frame_width / 2
#     center_y = frame_height / 2
#     drection_vector = scale(get_direction_vector_of_line(line), 200)
#     cv.line(frame, (int(center_x), int(center_y)), (int(drection_vector[0]) + int(center_x), int(center_y) - int(drection_vector[1])), (0,255,255), 2)

def display_direction_to_go(parallel_line_centers, frame):
    if(not isinstance(parallel_line_centers, (list, tuple, np.ndarray))):
        return
    if(len(parallel_line_centers) < 1):
        return
    line = parallel_line_centers[0]
    frame_width = frame.shape[1]
    frame_height = frame.shape[0]
    center_x = frame_width / 2
    center_y = frame_height / 2
    direction_to_go = scale(get_direction_to_go(line, frame), 50)
    cv.line(frame, (int(center_x), int(center_y)), (int(direction_to_go[0]) + int(center_x), int(center_y) - int(direction_to_go[1])), (0,69,255), 2)

def main():
    guard = True
    # cap = cv.VideoCapture('flash test.mp4')
    cap = cv.VideoCapture(0)
    img = np.zeros((25, 500, 3), np.uint8)
    cv.namedWindow('image')
    cv.createTrackbar('Blur', 'image', 5, 100, nothing)
    cv.createTrackbar('Block size', 'image', 5, 100, nothing)
    cv.createTrackbar('C', 'image', 5, 100, nothing)
    while cap.isOpened() and guard:
        ret, original_frame = cap.read()
        original_frame = cv.flip(original_frame, 1)
        original_frame = cv.rotate(original_frame, cv.ROTATE_90_CLOCKWISE)
        if not ret:
            print("Can't receive next frame")
            cap.set(cv.CAP_PROP_POS_FRAMES, 0)
            continue
        
        blur = cv.getTrackbarPos('Blur', 'image')
        block_size = cv.getTrackbarPos('Block size', 'image')
        c = cv.getTrackbarPos('C', 'image')
        processed_frame = process_frame(original_frame, blur, block_size, c)
        edges, lines = find_edges_and_lines(processed_frame)
        merged_lines = merge_lines(lines)
        parallel_line_centers = get_parallel_line_centers(merged_lines)

        if isinstance(lines, np.ndarray):
            cv.putText(original_frame, f'lines: {len(lines)}', (0,50), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv.LINE_AA)
            display_all_lines(lines, original_frame)
            display_merged_parallel_lines(merged_lines, original_frame)
            display_center_of_parallel_lines(parallel_line_centers, original_frame)
            display_displacement_and_direction_vectors(parallel_line_centers, original_frame)
            display_direction_to_go(parallel_line_centers, original_frame)

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