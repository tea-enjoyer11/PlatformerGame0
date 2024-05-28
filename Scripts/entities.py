import pygame
from pygame import Vector2, Surface

# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from tiles import Tile, ...


GROUND_FRICTION = 0.78


class PhysicsEntity:
    def __init__(self, pos: Vector2, size: Vector2) -> None:
        self.pos = pos
        self.size = size
        self.vel = Vector2(0)
