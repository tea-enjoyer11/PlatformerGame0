from typing import Sequence
from enum import Enum, auto
import pygame
import sys
from pygame import Vector2, Surface, Rect, Color

mainClock = pygame.time.Clock()
pygame.init()
screen = pygame.display.set_mode((800, 500), 0, 32)


class TileType(Enum):
    TILE = auto()
    RAMP_LEFT = auto()
    RAMP_RIGHT = auto()


class Tile:
    def __init__(self, color: Color, pos: Vector2, tile_type: TileType = TileType.TILE) -> None:
        if not isinstance(pos, Vector2):
            pos = Vector2(pos)
        self.color = color
        self.pos = pos
        self.type = tile_type


class Ramp(Tile):
    def __init__(self, color: Color, pos: Vector2, tile_type: TileType, elevation: float = 1) -> None:  # angegeben in wie TILESIZE einheit
        super().__init__(color, pos, tile_type)

        self.elevation = elevation


def collision_test(object_1: Rect, object_list: list[Rect]) -> list[Rect]:
    collision_list = []
    for obj in object_list:
        if obj.colliderect(object_1):
            collision_list.append(obj)
    return collision_list


TILESIZE = 50


def tile_rect(t: Tile | Ramp) -> Rect:
    if isinstance(t, Ramp):
        x = t.pos.x * TILESIZE
        y = (t.pos.y * TILESIZE) + TILESIZE - (TILESIZE * t.elevation)
        w = TILESIZE
        h = TILESIZE * t.elevation
        return Rect(x, y, w, h)
    else:  # isinstance(t, Tile)
        return Rect(t.pos.x * TILESIZE, t.pos.y * TILESIZE, TILESIZE, TILESIZE)


class Player():
    def __init__(self, pos: Vector2):
        self.pos = pos
        self.color = (0, 0, 255)
        self.rect = Rect(pos.x, pos.y, 25, 50)
        self.vertical_momentum = 0

        self.min_step_height = .3  # in TILESIZE Größe gerechnet

        self.last_pos = Vector2(0)

    def move(self, movement: Sequence[float], tiles: list[Tile]):
        self.last_pos = self.pos.copy()
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
            ramp_collision = self.rect.colliderect(hitbox)

            # TODO: Check einbauen, wo wenn man von der Seite auf die Ramp läuft, wo eigentlich die Wand ist, dass der Spieler da an der Kante hängen bleibt. (später min stepp offset einbauen)

            if ramp_collision:  # check if player collided with the bounding box for the ramp
                # get player's position relative to the ramp on the x axis
                rel_x = self.rect.x - hitbox.x
                max_ramp_height = TILESIZE * ramp.elevation
                ramp_height = 0  # eine Art offset height

                steppable = TILESIZE * ramp.elevation <= self.min_step_height * TILESIZE

                border_collision_threshold = 5
                if ramp.type == TileType.RAMP_RIGHT:
                    rel_x += self.rect.width
                    ramp_height = rel_x * ramp.elevation

                    # min. stepheight
                    rel_x_border = self.rect.x - (hitbox.x + TILESIZE)  # wie nah ist der Spieler an der Kante?
                    if movement[0] < 0 and (0 < abs(rel_x_border) <= border_collision_threshold) and not steppable:
                        ramp_height = 0
                        self.rect.left = hitbox.right
                        collision_types['left'] = True
                        self.pos[0] = self.rect.x
                elif ramp.type == TileType.RAMP_LEFT:
                    ramp_height = (TILESIZE * ramp.elevation) - rel_x * ramp.elevation

                    # min. stepheight
                    rel_x_border = self.rect.x - hitbox.x + self.rect.width  # wie nah ist der Spieler an der Kante?
                    if movement[0] > 0 and (0 < abs(rel_x_border) <= border_collision_threshold) and not steppable:
                        ramp_height = 0
                        self.rect.right = hitbox.left
                        collision_types['right'] = True
                        self.pos[0] = self.rect.x

                # constraints
                ramp_height = max(0, min(ramp_height, max_ramp_height))

                if 0 <= ramp.elevation <= 1:
                    target_y = hitbox.y + TILESIZE * ramp.elevation - ramp_height
                else:
                    hitbox_bottom_y = hitbox.y + hitbox.height
                    target_y = hitbox_bottom_y - ramp_height

                if self.rect.bottom > target_y:  # check if the player collided with the actual ramp
                    # adjust player height
                    self.rect.bottom = target_y
                    self.pos[1] = self.rect.y

                    collision_types['bottom'] = True

        # return collisions
        return collision_types


# generate test map
# tiles: list[Ramp | Tile] = [Tile("red", Vector2(0, 0)), Ramp('red', Vector2(3, 8), TileType.RAMP_RIGHT), Ramp('red', Vector2(5, 8), TileType.RAMP_RIGHT), Tile('red', Vector2(6, 8)), Tile('red', Vector2(4, 6)), Ramp('red', Vector2(4, 5), TileType.RAMP_LEFT), Tile('red', Vector2(3, 5))]
tiles: list[Ramp | Tile] = [Ramp("red", Vector2(2, 8), TileType.RAMP_RIGHT, 1), Ramp("red", Vector2(4, 8), TileType.RAMP_LEFT, 1), Ramp("red", Vector2(6, 8), TileType.RAMP_RIGHT, 0.5), Ramp("red", Vector2(8, 8), TileType.RAMP_LEFT, 0.5), Ramp("red", Vector2(10, 8), TileType.RAMP_RIGHT, 2), Ramp("red", Vector2(12, 8), TileType.RAMP_LEFT, 2)]
for i in range(16):
    tiles.append(Tile('red', Vector2(i, 9)))

p = Player(Vector2(100, 300))

right = False
left = False
speed = 5

# Loop ------------------------------------------------------- #
while True:

    # Background --------------------------------------------- #
    screen.fill((0, 0, 0))

    # Player ------------------------------------------------- #
    p.vertical_momentum += 1
    p.vertical_momentum = min(p.vertical_momentum, 15)
    player_movement = [0, p.vertical_momentum]

    if right:
        player_movement[0] += speed
    if left:
        player_movement[0] -= speed

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
            ground_height = t.pos.y * TILESIZE
            p1 = Vector2(t.pos.x * TILESIZE, (t.pos.y + 1) * TILESIZE)
            p2 = Vector2((t.pos.x + 1) * TILESIZE, (t.pos.y + 1) * TILESIZE)
            p3 = Vector2((t.pos.x + 1) * TILESIZE, (t.pos.y * TILESIZE) + TILESIZE - (TILESIZE * t.elevation))

            pygame.draw.polygon(screen, color, [p1, p2, p3])

            pygame.draw.rect(screen, "white", tile_rect(t), 3)

            # pygame.draw.polygon(screen, color, [[t.pos.x * TILESIZE, (t.pos.y + 1) * TILESIZE - 1], [(t.pos.x + 1) * TILESIZE - 1, (t.pos.y + 1) * TILESIZE - 1], [(t.pos.x + 1) * TILESIZE - 1, t.pos.y * TILESIZE]])
        elif t.type == TileType.RAMP_LEFT:
            color = "green"

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
            p2 = Vector2((t.pos.x + 1) * TILESIZE - 1, (t.pos.y + 1) * TILESIZE)  # -1 kann man eigentlich weglasse, nur mit siehts schöner aus. Irgendwie ist das ein bisschen länger als TILESIZE
            # p3 = Vector2(t.pos.x * TILESIZE, (t.pos.y + elev) * TILESIZE)
            p3 = Vector2(t.pos.x * TILESIZE, (t.pos.y * TILESIZE) + TILESIZE - (TILESIZE * t.elevation))

            pygame.draw.polygon(screen, color, [p1, p2, p3])

            pygame.draw.rect(screen, "white", tile_rect(t), 3)

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
            if event.key == pygame.K_TAB:
                speed = 5 if speed == 1 else 1
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_d:
                right = False
            if event.key == pygame.K_a:
                left = False

    # Update ------------------------------------------------- #
    pygame.display.update()
    mainClock.tick(60)
