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
DOWNSACLE_FACTOR = 3.5
DOWNSCALED_RES = RES / DOWNSACLE_FACTOR

pygame.init()
pygame.font.init()

master_screen = pygame.display.set_mode(RES, 0, 32)
screen = Surface(DOWNSCALED_RES)
mainClock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 21)

# IMGS = [load_image("assets/tile.png"), load_image("assets/ramp_left.png"), load_image("assets/ramp_right.png")]
# IMGS = [load_image("assets/tiles/grass/0.png"), load_image("assets/tiles/grass/3.png"), load_image("assets/tiles/grass/7.png")]

CUSTOM_TILES_HEIGHT_DATA = {}
CUSTOM_TILES_ORIENTATION_DATA = {}


def parse_master_tile_set_data(path: str, bg_color=(36, 0, 36)) -> None:
    master_tile_set = load_image(path)
    real_size = Vector2(master_tile_set.get_size())
    size = Vector2(real_size.x / TILESIZE, real_size.y / TILESIZE)
    offset_ = Vector2(2, 2)
    for y in range(int(size.y) - 2):
        for x in range(int(size.x) - 1):
            r = Rect(x * TILESIZE + offset_.x * x, y * TILESIZE + offset_.y * y, TILESIZE, TILESIZE)
            surf = master_tile_set.subsurface(r)
            ret: dict[int, int] = {}

            for x_ in range(TILESIZE):
                # v = 0
                t = 0  # thickness
                for y_ in range(TILESIZE):
                    c = surf.get_at((x_, y_))
                    if c == bg_color:
                        continue
                    else:
                        # v = y_
                        t += 1
                if t == 0:
                    ret[x_] = 0
                else:
                    ret[x_] = t

            idx = f"c_tile({x};{y})"
            CUSTOM_TILES_HEIGHT_DATA[idx] = ret
            # print(idx, ret)

            if ret[0] < ret[15]:
                CUSTOM_TILES_ORIENTATION_DATA[idx] = "left"
            else:
                CUSTOM_TILES_ORIENTATION_DATA[idx] = "right"


parse_master_tile_set_data("assets/tileset template.png")

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

    "TEST": load_image("assets/tiles/stone/3.png"),
    "TESTc_tile(1;14)": load_image("assets/tiles/grass/0.png"),
    "TESTc_tile(1;16)": load_image("assets/tiles/grass/4.png"),
    "TESTc_tile(2;14)": load_image("assets/tiles/grass/1.png"),
    "TESTc_tile(2;15)": load_image("assets/tiles/grass/2.png"),
    "TESTc_tile(2;16)": load_image("assets/tiles/grass/3.png"),
    "TESTc_tile(0;16)": load_image("assets/tiles/grass/5.png"),
    "TESTc_tile(0;15)": load_image("assets/tiles/grass/6.png"),
    "TESTc_tile(0;14)": load_image("assets/tiles/grass/7.png"),
    "TESTc_tile(1;15)": load_image("assets/tiles/grass/8.png"),
}


def parse_master_tile_set_surf(sheet: Surface):
    real_size = Vector2(sheet.get_size())
    size = Vector2(real_size.x / TILESIZE, real_size.y / TILESIZE)
    offset_ = Vector2(2, 2)
    ret: list[list[Surface]] = []
    for y in range(int(size.y) - 2):
        for x in range(int(size.x) - 1):
            r = Rect(x * TILESIZE + offset_.x * x, y * TILESIZE + offset_.y * y, TILESIZE, TILESIZE)
            IMGS[f"c_tile({x};{y})"] = sheet.subsurface(r)


parse_master_tile_set_surf(load_image("assets/tileset template.png"))
