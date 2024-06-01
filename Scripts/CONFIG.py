import pygame
from pygame import Vector2, Color, Rect, Surface
from enum import Enum, auto
from typing import Iterable, Hashable, Optional, Callable, Sequence

from Scripts.utils import load_image


TILESIZE = 32
CHUNKSIZE = 8
CHUNKWIDTH = CHUNKSIZE * TILESIZE

GROUND_FRICTION = 0.78


RES = Vector2(800, 600)

pygame.init()
pygame.font.init()

screen = pygame.display.set_mode(RES, 0, 32)
mainClock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 21)

# IMGS = [load_image("assets/tile.png"), load_image("assets/ramp_left.png"), load_image("assets/ramp_right.png")]
# IMGS = [load_image("assets/tiles/grass/0.png"), load_image("assets/tiles/grass/3.png"), load_image("assets/tiles/grass/7.png")]
IMGS = {
    0: load_image("assets/tile.png"),
    1: load_image("assets/ramp_left.png"),
    2: load_image("assets/ramp_right.png"),
    3: load_image("assets/custom_ramp.png"),
    4: load_image("assets/custom_ramp2.png"),
    5: load_image("assets/custom_ramp3.png"),
}
