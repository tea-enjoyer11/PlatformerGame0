# from timeit import timeit

# size = 100
# test_dict = {i: i for i in range(size)}

# time1 = timeit("[test_dict[i] for i in range(size)]", globals=globals())
# time2 = timeit("[test_dict.get(i) for i in range(size)]", globals=globals())

# print("[...] method:", time1)
# print(".get(...) method:", time2)


import time
import tracemalloc
import pygame
from pygame import Vector2
import pygame_gui
MAX_PARTICLE_STATE = 20


class Particle:
    def __init__(self, pos, vel, type) -> None:
        self.pos = pos
        self.vel = vel
        self.type = type
        self.state = 0

    def update(self, dt) -> bool:
        self.pos += self.vel * dt
        self.state += 1
        if self.state > MAX_PARTICLE_STATE:
            return False
        return True

    def render(self, screen, offset):
        ...


def main():
    dt = 0.016
    screen = pygame.display.set_mode((100, 100))
    # method 1
    tracemalloc.start()
    particles = []
    for i in range(1000):
        particles.append(Particle(Vector2(0, 0), Vector2(1, 1), 1))
    start = time.perf_counter()
    for i in range(MAX_PARTICLE_STATE):
        particles = [p for p in particles if p.update(dt)]
    dur = time.perf_counter() - start

    print("Methode 1 (Klassen) braucht:", dur, "sekunden")
    print(tracemalloc.get_traced_memory())

    # method 2
    tracemalloc.clear_traces()
    tracemalloc.start()
    particles = []
    for i in range(1000000):
        particles.append([Vector2(0, 0), Vector2(1, 1), 1])
    start = time.perf_counter()
    for i in range(MAX_PARTICLE_STATE):
        for p in particles:
            p[0] += p[1] * dt
    dur = time.perf_counter() - start

    print("Methode 2 (Listen) braucht: ", dur, "sekunden")
    print(tracemalloc.get_traced_memory())

    pygame.quit()


main()
