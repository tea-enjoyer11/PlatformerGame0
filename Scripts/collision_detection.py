from pygame import Rect
from typing import List, Tuple
import math

# region Sat collision methods + helpers


def get_vertices(r: Rect, angle: float) -> List[Tuple]:
    cx, cy = r.center
    theta = -math.radians(angle)
    rotated_corners = []
    corners = [
        (-r.w / 2, r.h / 2),
        (-r.w / 2, -r.h / 2),
        (r.w / 2, -r.h / 2),
        (r.w / 2, r.h / 2)
    ]

    for px, py in corners:
        rotated_x = cx + (px * math.cos(theta)) - (py * math.sin(theta))
        rotated_y = cy + (px * math.sin(theta)) + (py * math.cos(theta))
        rotated_corners.append((rotated_x, rotated_y))

    return rotated_corners


def normal_vector(vec: Tuple) -> Tuple:
    return (vec[1], -vec[0])


def vector_dot(vec1: Tuple, vec2: Tuple) -> float:
    # a x b = a1*b1 + a2*b2 + ... an + bn
    # return vec1[0] * vec2[0] + vec1[1] * vec2[1]
    return sum([vec1[i] * vec2[i] for i in range(len(vec1))])


def normalize_vector(vec: Tuple) -> Tuple:
    # v = v / ||v||
    l = sum(vec)
    if l:
        return (vec[0] / l, vec[1] / l)
    return (0, 0)


def sat(r1: Rect, r2: Rect, angle1: float, angle2: float) -> ...:
    vertices1 = get_vertices(r1, angle1)
    vertices2 = get_vertices(r2, angle2)
    axes: List[Tuple] = []
    axes += find_shape_normals(vertices1)
    axes += find_shape_normals(vertices2)

    # projection
    overlap = float("inf")
    smallest: Tuple = None
    for axis in axes:
        p1 = project_shape_onto_axis(vertices1, axis)
        p2 = project_shape_onto_axis(vertices2, axis)
        # do the projections overlap?
        overlap_b = projections_overlap(p1, p2)
        # print(overlap, p1, p2)
        if not overlap_b:
            return False, 0, None  # , []
        else:
            o = get_projections_overlap(p1, p2)
            print(o, axis)
            if o < overlap:
                overlap = o
                smallest = axis
    # intersection_points = find_intersection_points()
    return True, overlap, smallest  # , intersection_points


def find_shape_normals(vertices: List[Tuple]) -> List[Tuple]:
    axes = []
    for i, vertex in enumerate(vertices):
        p1 = vertex
        p2 = vertices[0 if i + 1 == len(vertices) else i + 1]
        edge = (p1[0] - p2[0], p1[1] - p2[1])
        normal = normalize_vector(normal_vector(edge))
        axes.append(normal)
    return axes


def project_shape_onto_axis(vertices: List[Tuple], axis: Tuple) -> Tuple:
    min_proj = float("inf")
    max_proj = -float("inf")

    for vertex in vertices:
        # p = Vector2(vertex).dot(Vector2(axis))
        p = vector_dot(vertex, axis)
        min_proj = min(min_proj, p)
        max_proj = max(max_proj, p)
    return (min_proj, max_proj)


def projections_overlap(p1: Tuple, p2: Tuple) -> bool:
    # x = min, y = max
    return p1[1] >= p2[0] and p2[1] >= p1[0]


def get_projections_overlap(p1: Tuple, p2: Tuple) -> float:
    # x = min, y = max
    return p1[1] - p2[0]
# endregion
