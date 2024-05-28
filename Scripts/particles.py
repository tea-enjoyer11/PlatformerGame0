import pygame
from typing import Callable, Hashable, Sequence, Iterable, Optional


class ImageCache:
    def __init__(self, make_image_func: Callable[[Hashable], pygame.Surface]):
        self.cache: dict[Hashable, pygame.Surface] = {}
        self.misses = 0
        self.make_image = make_image_func

    def get_image(self, item: Hashable) -> pygame.Surface:
        if item not in self.cache:
            self.misses += 1
            self.cache[item] = self.make_image(item)
        return self.cache[item]


class Particle:
    def update(self, dt: float, *args, **kwargs) -> bool:
        """Return False when particle should be removed."""
        return True

    def draw_pos(self, image: pygame.Surface) -> Sequence[float]:
        raise NotImplementedError

    def cache_lookup(self) -> Hashable:
        raise NotImplementedError


class ParticleGroup:
    def __init__(self, image_cache: ImageCache, blend: int = pygame.BLENDMODE_NONE,
                 particles: Optional[list[Particle]] = None):
        self.particles: list[Particle] = particles if particles is not None else []
        self.image_cache = image_cache
        self.blend = blend

    def __len__(self):
        return len(self.particles)

    def clear(self) -> None:
        self.particles.clear()

    def add(self, particles: Particle | Iterable[Particle]):
        if isinstance(particles, Particle):
            self.particles.append(particles)
        else:
            self.particles.extend(particles)

    def update(self, dt: float, *args, **kwargs):
        self.particles = [p for p in self.particles if p.update(dt, *args, **kwargs)]

    def _get_draw_tuple(self, p: Particle) -> tuple[pygame.Surface, Sequence[float]]:
        image = self.image_cache.get_image(p.cache_lookup())
        return image, p.draw_pos(image)

    def _in_range(self, pos: tuple, boundary: tuple) -> bool:

        return False

    def draw(self, screen: pygame.Surface, blend: int = pygame.BLENDMODE_NONE):
        screen.fblits([self._get_draw_tuple(p) for p in self.particles], blend if blend else self.blend)

    def draw2(self, screen: pygame.Surface, blend: int = pygame.BLENDMODE_NONE):
        # VIIEEEELLL ZU LANGSAM
        arr = []
        boundary = screen.get_size()
        for p in self.particles:
            draw_tuple = self._get_draw_tuple(p)
            if draw_tuple[1][0] not in range(boundary[0]) or draw_tuple[1][1] not in range(boundary[1]):
                arr.append(draw_tuple)
        screen.fblits(arr, blend if blend else self.blend)


class CircleParticle(Particle):
    def __init__(self, pos: tuple, vel: tuple, max_imgs: int, type: str = "particle") -> None:
        self.type = type
        self.pos = pos
        self.vel = vel
        self.max_ints = max_imgs
        self.state = 0  # which img to use right now?

    def update(self, dt: float, *args, **kwargs) -> bool:
        self.pos = (self.pos[0] + self.vel[0] * dt, self.pos[1] + self.vel[1] * dt)
        self.state += dt * 10
        if self.state > self.max_ints - 1:
            return False
        return True

    def draw_pos(self, image: pygame.Surface) -> Sequence[float]:
        # img benötigt um zu centern, falls gewollt
        return self.pos

    def cache_lookup(self) -> Hashable:
        return f"assets/particles/{self.type}/{int(self.state)}.png"


class LeafParticle(Particle):
    def __init__(self, pos: tuple, vel: tuple, max_imgs: int, type: str = "leaf") -> None:
        self.type = type
        self.pos = pos
        self.vel = vel
        self.max_ints = max_imgs
        self.state = 0  # which img to use right now?

    def update(self, dt: float, *args, **kwargs) -> bool:
        self.pos = (self.pos[0] + self.vel[0] * dt, self.pos[1] + self.vel[1] * dt)
        self.state += dt * 10
        if self.state > self.max_ints - 1:
            return False
        return True

    def draw_pos(self, image: pygame.Surface) -> Sequence[float]:
        # img benötigt um zu centern, falls gewollt
        return self.pos

    def cache_lookup(self) -> Hashable:
        s = str(int(self.state))
        if len(s) < 2:
            s = "0" + s
        return f"assets/particles/{self.type}/{s}.png"
