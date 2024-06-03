import pygame
from pygame import Vector2, Color, Rect, Surface
from enum import Enum, auto
from typing import Iterable, Hashable, Optional, Callable, Sequence

from Scripts.utils import load_image, save_compressed_pickle, save_pickle, load_compressed_pickle, load_pickle


TILESIZE = 32
CHUNKSIZE = 8
CHUNKWIDTH = CHUNKSIZE * TILESIZE

GROUND_FRICTION = 0.78
AIR_FRICTION = 0.98

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
    33: load_image("assets/custom_ramp.png", flip_x=True),
    4: load_image("assets/custom_ramp2.png"),
    44: load_image("assets/custom_ramp2.png", flip_x=True),
    5: load_image("assets/custom_ramp3.png"),
    55: load_image("assets/custom_ramp3.png", flip_x=True),

    "grass0": load_image("assets/tiles/grass0.png"),
    "grass1": load_image("assets/tiles/grass1.png"),
    "grass2": load_image("assets/tiles/grass2.png"),
    "grass3": load_image("assets/tiles/grass3.png"),
    "grass4": load_image("assets/tiles/grass4.png"),
    "grass5": load_image("assets/tiles/grass5.png"),
    "grass6": load_image("assets/tiles/grass6.png"),
}
