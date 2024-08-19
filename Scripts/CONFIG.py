import pygame
from pygame import Vector2, Color, Rect, Surface, FRect, Mask
from pygame.mask import from_surface, from_threshold
from enum import Enum, auto
from typing import Iterable, Hashable, Optional, Callable, Sequence
from Scripts.sprites import cut_from_spritesheet

from Scripts.utils import load_image, save_compressed_pickle, save_pickle, load_compressed_pickle, load_pickle


TILESIZE = 16
CHUNKSIZE = 8
CHUNKWIDTH = CHUNKSIZE * TILESIZE

GROUND_FRICTION = 0.78
AIR_FRICTION = 0.98

RES = Vector2(800, 600)
DOWNSACLE_FACTOR = 3
DOWNSCALED_RES = RES / DOWNSACLE_FACTOR

pygame.init()
pygame.font.init()

master_screen = pygame.display.set_mode(RES, 0, 32)
screen = Surface(DOWNSCALED_RES)
mainClock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 21)
