import pygame
import math
from pygame import Rect, Vector2, Surface
from typing import Tuple, List

pygame.font.init()
sysfont = pygame.font.SysFont("arial", 24)


def draw_text(surf: Surface, text: str, pos: Tuple, color=(255, 255, 255)):
    textsurface = sysfont.render(text, True, color)
    surf.blit(textsurface, pos)


def get_vertices(r: Rect, angle: float) -> list[Tuple]:
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
        rotated_corners.append(Vector2(rotated_x, rotated_y))

    return rotated_corners


def normal_vector(vec: Vector2) -> Vector2:
    return Vector2(vec.y, -vec.x)


def sat(rect1: Rect, rect2: Rect, angle1: float, angle2: float) -> ...:
    vertices1 = get_vertices(rect1, angle1)
    vertices2 = get_vertices(rect2, angle2)
    axes: List[Vector2] = []
    axes += find_shape_normals(vertices1)
    axes += find_shape_normals(vertices2)

    # projection
    overlap = float("inf")
    smallest = None
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
            if o < overlap:
                overlap = o
                smallest = axis
    # intersection_points = find_intersection_points()
    return True, overlap, smallest  # , intersection_points


# def find_intersection_points(): ...


def find_shape_normals(vertices: List[Tuple]) -> List[Vector2]:
    axes = []
    for i, vertex in enumerate(vertices):
        p1 = vertex
        p2 = vertices[0 if i + 1 == len(vertices) else i + 1]
        edge = Vector2(p1) - Vector2(p2)
        normal = normal_vector(edge).normalize()
        axes.append(normal)
    return axes


def project_shape_onto_axis(vertices: List[Vector2], axis: Vector2) -> Vector2:
    min_proj = float("inf")
    max_proj = -float("inf")
    for vertex in vertices:
        p = Vector2(vertex).dot(axis)
        # print(p)
        min_proj = min(min_proj, p)
        max_proj = max(max_proj, p)
    return Vector2(min_proj, max_proj)


def projections_overlap(p1: Vector2, p2: Vector2) -> bool:
    # x = min, y = max
    return p1.y >= p2.x and p2.y >= p1.x


def get_projections_overlap(p1: Vector2, p2: Vector2) -> float:
    # x = min, y = max
    return p1.y - p2.x


pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

tilemap_surface = pygame.image.load('assets/test/test-tilemap.png')
tilemap_rect = tilemap_surface.get_rect(center=(400, 300))
player_rect = pygame.Rect(50, 50, 20, 40)

angle = 0
player_angle = 0
r = False
running = True
while running:
    dt = clock.tick(0) * .001

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            r = not r
    if r:
        angle = (angle - 100 * dt) % 360

    screen.fill((0, 0, 0))
    player_rect.topleft = pygame.mouse.get_pos()

    rotated_tilemap_surface = pygame.transform.rotate(tilemap_surface, angle)
    rotated_tilemap_rect = rotated_tilemap_surface.get_rect(center=tilemap_rect.center)
    screen.blit(tilemap_surface, tilemap_rect.topleft)
    screen.blit(rotated_tilemap_surface, rotated_tilemap_rect.topleft)
    pygame.draw.rect(screen, (125, 20, 84), player_rect)
    sat_res = sat(tilemap_rect, player_rect, angle, player_angle)

    x = get_vertices(tilemap_rect, angle)
    for i, p in enumerate(x):
        pygame.draw.line(screen, (255, 255, 255), p, x[0 if i + 1 == len(x) else i + 1])

    draw_text(screen, f"{sat_res}", (10, 10))
    draw_text(screen, f"{clock.get_fps():.0f}", (10, 30))
    pygame.display.flip()

pygame.quit()
