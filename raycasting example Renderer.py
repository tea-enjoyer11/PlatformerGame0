# https://www.youtube.com/watch?v=TOEi6T2mtHo
from Scripts.utils_math import dist
import math
import pygame
from pygame import Vector2, Surface
import random

from Renderer_Engine import GameTemplate, Coordinate


class Boundary:
    def __init__(self, p1: Vector2, p2: Vector2) -> None:
        self.p1 = p1
        self.p2 = p2

    def render(self, surface: Surface):
        pygame.draw.line(surface, "white", self.p1, self.p2, 1)


class Ray:
    def __init__(self, pos: Vector2, dir: Vector2) -> None:
        self.pos = pos
        # self.dir = Vector2(math.cos(angle), math.sin(angle)) * 10
        self.dir = dir
        if self.dir.length() != 0:
            self.dir = self.dir.normalize()
        self.angle = math.atan2(self.dir.y, self.dir.x) % 360

    def set_pos(self, pos: Vector2):
        self.pos = pos

    def lookat(self, p: Vector2):
        self.dir = p - self.pos

    def render(self, surface: Surface):
        pygame.draw.line(surface, "yellow", self.pos, self.pos + self.dir, 1)

    def cast(self, b: Boundary) -> Vector2 | None:
        x1 = b.p1.x
        y1 = b.p1.y
        x2 = b.p2.x
        y2 = b.p2.y

        x3 = self.pos.x
        y3 = self.pos.y
        x4 = self.pos.x + self.dir.x
        y4 = self.pos.y + self.dir.y

        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if den == 0:  # parallel
            return None

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den

        if 0 < t < 1 and u > 0:
            p = Vector2(0)
            p.x = x1 + t * (x2 - x1)
            p.y = y1 + t * (y2 - y1)
            return p
        else:
            return None


class Particle:
    def __init__(self, pos: Vector2) -> None:
        self.pos = pos
        self.rays: list[Ray] = []

    def update_rays(self, walls: list[Boundary]):
        self.rays = []
        for b in walls:
            self.rays.append(Ray(self.pos, (b.p1 - self.pos - Vector2(0.00001))))
            self.rays.append(Ray(self.pos, (b.p1 - self.pos)))
            self.rays.append(Ray(self.pos, (b.p1 - self.pos + Vector2(0.00001))))

            self.rays.append(Ray(self.pos, (b.p2 - self.pos - Vector2(0.00001))))
            self.rays.append(Ray(self.pos, (b.p2 - self.pos)))
            self.rays.append(Ray(self.pos, (b.p2 - self.pos + Vector2(0.00001))))

    def cast(self, walls: list[Boundary]) -> list[Vector2]:
        l = []
        for r in self.rays:
            closest = None
            record = math.inf
            for b in walls:
                p = r.cast(b)
                if p:
                    dis = dist(self.pos, p)
                    if (dis < record):
                        record = dis
                        closest = p

            if closest:
                l.append((closest, r.angle))

        l = sorted(l, key=lambda x: x[1])
        return [point for point, angle in l]

    def render(self, screen: Surface):
        pygame.draw.circle(screen, "red", self.pos, 5)
        # [r.render(screen) for r in self.rays]

    def move(self, pos: Vector2):
        self.pos = pos
        [r.set_pos(pos) for r in self.rays]


class App(GameTemplate):
    def __init__(self, size: Coordinate, flags=0, depth=0, display=0, vsync=0):
        super().__init__(size, flags, depth, display, vsync)
        # self.walls = [Boundary(Vector2(random.randint(20, 380), random.randint(20, 380)), Vector2(random.randint(20, 380), random.randint(20, 380))) for _ in range(5)]
        self.walls = [Boundary(Vector2(300, 100), Vector2(300, 300)), Boundary(Vector2(100, 100), Vector2(200, 200))]
        self.walls.extend([Boundary(Vector2(0, 0), Vector2(0, 400)), Boundary(Vector2(0, 400), Vector2(400, 400)), Boundary(Vector2(400, 400), Vector2(400, 0)), Boundary(Vector2(400, 0), Vector2(0, 0))])
        self.part = Particle(Vector2(100, 200))
        self.part.update_rays(self.walls)
        self.mpos = Vector2()

    def update(self) -> float:
        dt = super().update()
        self.mpos = Vector2(pygame.mouse.get_pos())

        self.part.move(self.mpos)
        self.part.update_rays(self.walls)

        pygame.display.set_caption(f"{self.clock.get_fps():.0f}")

    def render(self) -> None:
        self.screen.fill("black")

        intersects = self.part.cast(self.walls)
        pygame.draw.polygon(self.screen, (50, 50, 50), intersects)

        for p in intersects:
            pygame.draw.circle(self.screen, "blue", p, 4)
            pygame.draw.line(self.screen, "yellow", self.part.pos, p, 2)

        [b.render(self.screen) for b in self.walls]
        self.part.render(self.screen)

        pygame.display.flip()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.walls = [Boundary(Vector2(random.randint(20, 380), random.randint(20, 380)), Vector2(random.randint(20, 380), random.randint(20, 380))) for _ in range(5)]
                    self.walls.extend([Boundary(Vector2(0, 0), Vector2(0, 400)), Boundary(Vector2(0, 400), Vector2(400, 400)), Boundary(Vector2(400, 400), Vector2(400, 0)), Boundary(Vector2(400, 0), Vector2(0, 0))])


App((400, 400)).run()

#! Blog über perfektes Raycasting:
#! https://ncase.me/sight-and-light/
