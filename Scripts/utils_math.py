from pygame import Vector2


def lerp(start: float, end: float, time: float) -> float:
    return start + (end - start) * time


def Vector2Lerp(start: Vector2, end: Vector2, time: float) -> Vector2:
    return start + (end - start) * time


def dist(p1: Vector2, p2: Vector2) -> float:
    return ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1])) ** 0.5


def clamp(minimum, x, maximum):
    return max(minimum, min(x, maximum))


def clamp_bottom(minimun, x):
    return max(minimun, x)


def clamp_top(maximun, x):
    return min(maximun, x)


def cycle_sequence(arr: list | tuple) -> list | tuple:
    first = arr[0]
    arr[0] = arr[-1]
    arr[-1] = first
    return arr


def flatten_list(l: list):
    l_ = []
    if not isinstance(l, list | tuple):
        return []
    else:
        for i in l:
            if isinstance(i, list | tuple):  # Check if element is a list
                l_ += flatten_list(i)  # Recursively flatten nested list
            else:
                l_.append(i)
    return l_


def reverseInts(list_: list) -> list:
    listCopy = []
    for pos in list_:
        if pos > 0:
            listCopy.append(-pos)
        else:
            listCopy.append(pos * -1)

    return listCopy
