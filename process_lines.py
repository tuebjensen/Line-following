from statistics import median
from typing import Union


class Line:
    _rho_diff_threshold = 80.0
    _theta_diff_threshold = 0.3

    def __init__(self, rho: float, theta: float) -> 'Line':
        self.rho = rho
        self.theta = theta

    def is_similar(self, to_compare: 'Line') -> bool:
        return (abs(self.rho - to_compare.rho) < self._rho_diff_threshold 
                and abs(self.theta - to_compare.theta) < self._theta_diff_threshold)



def get_from_houghlines(hough_lines) -> 'list[Line]':
    if hough_lines is None:
        return None
    lines = []
    for line in hough_lines:
        rho, theta = line[0]
        lines.append(Line(rho, theta))
    return lines


def merge_lines(lines: 'list[Line]') -> 'list[Line]':
    similar_lines: dict[Line, list[Line]] = {}
    for line in lines:
        found_similar = False
        for group_leading_line, grouped_lines in similar_lines.items():
            if line.is_similar(group_leading_line):
                found_similar = True
                grouped_lines.append(line)
                break
        if not found_similar:
            similar_lines[line] = [line]

    merged_lines = []
    for grouped_lines in list(similar_lines.values()):
        merged_lines.append(_get_median_line(grouped_lines))
    return merged_lines


def _get_median_line(lines: 'list[Line]') -> 'Line':
    rhos = []
    thetas = []
    for line in lines:
        rhos.append(line.rho)
        thetas.append(line.theta)
    median_rho = median(rhos)
    median_theta = median(thetas)
    return Line(median_rho, median_theta)


def get_centers_of_parallel_line_pairs(lines: 'list[Line]') -> 'list[Line]':
    if lines is None:
        return None
    parallel_lines: dict[float, list[Line]] = {}
    for line in lines:
        found_parallel = False
        for parallel_line_angle, same_angle_lines in parallel_lines.items():
            if(abs(line.theta - parallel_line_angle) < 2*Line._theta_diff_threshold):
                same_angle_lines.append(line)
                found_parallel = True
                break
        if not found_parallel:
            parallel_lines[line.theta] = [line]

    center_lines: list[Line] = []
    for same_angle_lines in list(parallel_lines.values()):
        if(len(same_angle_lines) != 2):
            return
        center_lines.append(_get_center_line(same_angle_lines[0], same_angle_lines[1]))
    return center_lines


def _get_center_line(line_one: 'Line', line_two: 'Line') -> 'Line':
    mean_rho = (line_one.rho + line_two.rho) / 2
    mean_theta = (line_one.theta + line_two.theta) / 2
    return Line(mean_rho, mean_theta)
