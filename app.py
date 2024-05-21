#!/usr/bin/python3.4
# Setup Python ----------------------------------------------- #
from typing import Sequence
from enum import Enum, auto
import pygame
import sys
from pygame import Vector2, Surface, Rect, Color

# Setup pygame/window ---------------------------------------- #
mainClock = pygame.time.Clock()
pygame.init()
pygame.display.set_caption('rampy boi')
screen = pygame.display.set_mode((500, 500), 0, 32)


class TileType(Enum):
    TILE = auto()
    RAMP_LEFT = auto()
    RAMP_RIGHT = auto()


class Tile:
    def __init__(self, color: Color, pos: Vector2, tile_type: TileType = TileType.TILE) -> None:
        self.color = color
        self.pos = pos
        self.type = tile_type


class Ramp(Tile):
    def __init__(self, color: Color, pos: Vector2, tile_type: TileType, elevation: float = 0.0) -> None:  # 0 = default = 45 grad; 0.5 = 22,5 (45/2) grad; 0.75 = 11,25 (45/4) grad
        super().__init__(color, pos, tile_type)

        self.elevation = elevation


class tile():
    def __init__(self, pos, tile_type, ramp=0):  # 0 = none, 1 = right, 2 = left
        self.pos = pos
        self.type = tile_type
        self.ramp = ramp


def collision_test(object_1: Rect, object_list: list[Rect]) -> list[Rect]:
    collision_list = []
    for obj in object_list:
        if obj.colliderect(object_1):
            collision_list.append(obj)
    return collision_list


TILESIZE = 50


def tile_rect(t: Tile) -> Rect:
    return Rect(t.pos.x * TILESIZE, t.pos.y * TILESIZE, TILESIZE, TILESIZE)


class player():
    def __init__(self, pos: Vector2):
        self.pos = pos
        self.color = (0, 0, 255)
        self.rect = Rect(pos.x, pos.y, 25, 50)
        self.vertical_momentum = 0

    def move(self, movement: Sequence[float], tiles: list[tile]):
        normal_tiles = [tile_rect(t) for t in tiles if t.type == TileType.TILE]  # make list of all normal tile rects
        ramps: list[Ramp] = [t for t in tiles if t.type in [TileType.RAMP_LEFT, TileType.RAMP_RIGHT]]  # make list of all ramps

        # handle standard collisions
        collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}
        self.pos[0] += movement[0]
        self.rect.x = int(self.pos[0])
        tile_hit_list = collision_test(self.rect, normal_tiles)
        for t in tile_hit_list:
            if movement[0] > 0:
                self.rect.right = t.left
                collision_types['right'] = True
            elif movement[0] < 0:
                self.rect.left = t.right
                collision_types['left'] = True
            self.pos[0] = self.rect.x
        self.pos[1] += movement[1]
        self.rect.y = int(self.pos[1])
        tile_hit_list = collision_test(self.rect, normal_tiles)
        for t in tile_hit_list:
            if movement[1] > 0:
                self.rect.bottom = t.top
                collision_types['bottom'] = True
            elif movement[1] < 0:
                self.rect.top = t.bottom
                collision_types['top'] = True
            self.pos[1] = self.rect.y

        # handle ramps
        for ramp in ramps:
            hitbox = tile_rect(ramp)
            if self.rect.colliderect(hitbox):  # check if player collided with the bounding box for the ramp
                # get player's position relative to the ramp on the x axis
                rel_x = self.rect.x - hitbox.x

                # get height at player's position based on type of ramp
                if ramp.type == TileType.RAMP_RIGHT:
                    pos_height = (rel_x + self.rect.width) * (1 - ramp.elevation)  # go by player right edge on right ramps
                elif ramp.type == TileType.RAMP_LEFT:
                    pos_height = (TILESIZE - rel_x) * (1 - ramp.elevation)  # is already left edge by default

                # add constraints
                pos_height = min(pos_height, TILESIZE)
                pos_height = max(pos_height, 0)

                target_y = hitbox.y + TILESIZE - pos_height

                if self.rect.bottom > target_y:  # check if the player collided with the actual ramp
                    # adjust player height
                    self.rect.bottom = target_y
                    self.pos[1] = self.rect.y

                    collision_types['bottom'] = True

        # return collisions
        return collision_types


# generate test map
tiles: list[Ramp | Tile] = [Ramp('red', Vector2(3, 8), TileType.RAMP_RIGHT), Ramp('red', Vector2(5, 8), TileType.RAMP_RIGHT), Tile('red', Vector2(6, 8)), Tile('red', Vector2(4, 6)), Ramp('red', Vector2(4, 5), TileType.RAMP_LEFT), Tile('red', Vector2(3, 5))]
for i in range(10):
    tiles.append(Tile('red', Vector2(i, 9)))

p = player(Vector2(100, 300))

right = False
left = False

# Loop ------------------------------------------------------- #
while True:

    # Background --------------------------------------------- #
    screen.fill((0, 0, 0))

    # Player ------------------------------------------------- #
    p.vertical_momentum += 1
    p.vertical_momentum = min(p.vertical_momentum, 15)
    player_movement = [0, p.vertical_momentum]

    if right:
        player_movement[0] += 5
    if left:
        player_movement[0] -= 5

    collisions = p.move(player_movement, tiles)
    if (collisions['bottom']) or (collisions['top']):
        p.vertical_momentum = 0

    pygame.draw.rect(screen, p.color, p.rect)

    # Tiles -------------------------------------------------- #
    for t in tiles:
        color = t.color
        if t.type == TileType.TILE:
            pass
            pygame.draw.rect(screen, color, tile_rect(t))
        elif t.type == TileType.RAMP_RIGHT:
            color = "yellow"

            """
                          p3
                        / |
                      /   |
                    /     |
                  /       |
                /         |
              /           |
            p1 ---------- p2
            """
            elev = t.elevation
            p1 = Vector2(t.pos.x * TILESIZE, (t.pos.y + 1) * TILESIZE)
            p2 = Vector2((t.pos.x + 1) * TILESIZE, (t.pos.y + 1) * TILESIZE)
            p3 = Vector2((t.pos.x + 1) * TILESIZE, (t.pos.y + elev) * TILESIZE)

            pygame.draw.polygon(screen, color, [p1, p2, p3])

            # pygame.draw.polygon(screen, color, [[t.pos.x * TILESIZE, (t.pos.y + 1) * TILESIZE - 1], [(t.pos.x + 1) * TILESIZE - 1, (t.pos.y + 1) * TILESIZE - 1], [(t.pos.x + 1) * TILESIZE - 1, t.pos.y * TILESIZE]])
        elif t.type == TileType.RAMP_LEFT:
            color = "yellow"

            """
            p3
            | \
            |   \
            |     \
            |       \
            |         \
            |           \
            p1 ---------- p2
            """
            elev = t.elevation
            p1 = Vector2(t.pos.x * TILESIZE, (t.pos.y + 1) * TILESIZE)
            p2 = Vector2((t.pos.x + 1) * TILESIZE, (t.pos.y + 1) * TILESIZE)
            p3 = Vector2(t.pos.x * TILESIZE, (t.pos.y + elev) * TILESIZE)

            pygame.draw.polygon(screen, color, [p1, p2, p3])

            # pygame.draw.polygon(screen, color, [[t.pos.x * TILESIZE, (t.pos.y + 1) * TILESIZE - 1], [(t.pos.x + 1) * TILESIZE - 1, (t.pos.y + 1) * TILESIZE - 1], [t.pos.x * TILESIZE, (t.pos.y) * TILESIZE]])

    # Buttons ------------------------------------------------ #
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            if event.key == pygame.K_d:
                right = True
            if event.key == pygame.K_a:
                left = True
            if event.key == pygame.K_SPACE:
                p.vertical_momentum = -16
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_d:
                right = False
            if event.key == pygame.K_a:
                left = False

    # Update ------------------------------------------------- #
    pygame.display.update()
    mainClock.tick(60)
