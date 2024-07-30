import math


def calc_distance(dest_loc: list[int], point_loc: list[int]) -> float:
    return math.sqrt(
        (dest_loc[0] - point_loc[0])**2 + (dest_loc[1] - point_loc[1])**2
    )
