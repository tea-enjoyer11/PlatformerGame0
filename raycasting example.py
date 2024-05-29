import math
import pygame
from pygame import Vector2, Surface
import random
screen = pygame.display.set_mode((400, 400))
clock = pygame.time.Clock()


class Boundary:
    def __init__(self, p1: Vector2, p2: Vector2) -> None:
        self.p1 = p1
        self.p2 = p2

    def render(self, surface: Surface):
        pygame.draw.line(surface, "white", self.p1, self.p2, 1)


class Ray:
    def __init__(self, pos: Vector2, angle: float) -> None:
        self.pos = pos
        self.dir = Vector2(math.cos(angle), math.sin(angle)) * 10

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

        for a in range(0, 360, 10):
            self.rays.append(Ray(self.pos, math.radians(a)))

    def cast(self, walls: list[Boundary]) -> list[Vector2]:
        l = []
        for r in self.rays:
            for b in walls:
                p = r.cast(b)
                if p:
                    l.append(p)
        return l

    def render(self, screen: Surface):
        pygame.draw.circle(screen, "red", self.pos, 5)
        # [r.render(screen) for r in self.rays]

    def move(self, pos: Vector2):
        self.pos = pos
        [r.set_pos(pos) for r in self.rays]


walls = [Boundary(Vector2(random.randint(20, 380), random.randint(20, 380)), Vector2(random.randint(20, 380), random.randint(20, 380))) for _ in range(5)]
part = Particle(Vector2(100, 200))

while True:
    dt = clock.tick(0) * 0.001
    mpos = Vector2(pygame.mouse.get_pos())

    screen.fill("black")
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            exit()

    part.move(mpos)

    for p in part.cast(walls):
        pygame.draw.circle(screen, "blue", p, 4)
        pygame.draw.line(screen, "yellow", part.pos, p, 2)

    [b.render(screen) for b in walls]
    part.render(screen)
    pygame.display.flip()

# https://youtu.be/TOEi6T2mtHo?t=1700
