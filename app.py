from typing import Sequence
from enum import Enum, auto
import pygame
import sys
from pygame import Vector2, Surface, Rect, Color

mainClock = pygame.time.Clock()
pygame.init()
pygame.font.init()
screen = pygame.display.set_mode((800, 500), 0, 32)
font = pygame.font.SysFont("arial", 21)


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


def render_collision_mesh(surf: Surface, color: Color, t: Tile | Ramp, width: int = 1) -> None:
    if isinstance(t, Ramp):
        r = tile_rect(t)
        p1, p2 = r.bottomleft, r.topright
        if t.type == TileType.RAMP_LEFT:
            p1, p2 = r.bottomright, r.topleft
        pygame.draw.rect(surf, color, r, width)
        pygame.draw.line(surf, color, p1, p2, width)
    else:  # isinstance(t, Tile)
        r = tile_rect(t)
        pygame.draw.rect(surf, color, r, width)


class Player():
    def __init__(self, pos: Vector2):
        self.pos = pos
        self.color = (0, 0, 255)
        self.rect = Rect(pos.x, pos.y, 25, 50)
        self.vertical_momentum = 0

        self.min_step_height = 1  # in TILESIZE Größe gerechnet

        self._last_pos = Vector2(0)

        self._collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}
        self._last_collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}

    def move(self, movement: Sequence[float], tiles: list[Tile]):
        self._last_pos = self.pos.copy()
        self._last_collision_types = self._collision_types.copy()
        normal_tiles = [tile_rect(t) for t in tiles if t.type == TileType.TILE]  # make list of all normal tile rects
        ramps: list[Ramp] = [t for t in tiles if t.type in [TileType.RAMP_LEFT, TileType.RAMP_RIGHT]]  # make list of all ramps

        # handle standard collisions
        collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}
        self.pos[0] += movement[0]
        self.rect.x = int(self.pos[0])
        tile_hit_list = collision_test(self.rect, normal_tiles)
        for t in tile_hit_list:
            top_point = t.y - t.height
            steppable = top_point - (self.pos.y) <= self.min_step_height * TILESIZE
            if movement[0] > 0:
                self.rect.right = t.left
                collision_types['right'] = True
                if steppable is True and self._last_collision_types["bottom"] is True:
                    self.rect.bottom = t.top
                    collision_types['bottom'] = True
                    self.pos[1] = self.rect.y - 1  # kleiner offset, damit der Spieler nicht an der Kante stecken bleibt
            elif movement[0] < 0:
                self.rect.left = t.right
                collision_types['left'] = True
                if steppable and self._last_collision_types["bottom"]:
                    self.rect.bottom = t.top
                    collision_types['bottom'] = True
                    self.pos[1] = self.rect.y - 1  # kleiner offset, damit der Spieler nicht an der Kante stecken bleibt
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
        self._collision_types = collision_types
        return collision_types


# generate test map
tiles: list[Ramp | Tile] = [Tile("red", Vector2(0, 0)), Ramp('red', Vector2(3, 8), TileType.RAMP_RIGHT), Ramp('red', Vector2(5, 8), TileType.RAMP_RIGHT), Ramp('red', Vector2(7, 8), TileType.RAMP_LEFT, 0.5), Tile('red', Vector2(6, 8)), Tile('red', Vector2(4, 6)), Ramp('red', Vector2(4, 5), TileType.RAMP_LEFT), Tile('red', Vector2(3, 5)), Tile("red", Vector2(11, 8)), Tile("red", Vector2(14, 8)), Tile("red", Vector2(14, 7))]
# tiles: list[Ramp | Tile] = [Ramp("red", Vector2(2, 8), TileType.RAMP_RIGHT, 1), Ramp("red", Vector2(4, 8), TileType.RAMP_LEFT, 1), Ramp("red", Vector2(6, 8), TileType.RAMP_RIGHT, 0.5), Ramp("red", Vector2(8, 8), TileType.RAMP_LEFT, 0.5), Ramp("red", Vector2(10, 8), TileType.RAMP_RIGHT, 2), Ramp("red", Vector2(12, 8), TileType.RAMP_LEFT, 2)]
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
            """Skizze
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
            p3 = Vector2((t.pos.x + 1) * TILESIZE, (t.pos.y * TILESIZE) + TILESIZE - (TILESIZE * t.elevation))

            pygame.draw.polygon(screen, color, [p1, p2, p3])

            render_collision_mesh(screen, "white", t, 3)

        elif t.type == TileType.RAMP_LEFT:
            """Skizze
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
            p3 = Vector2(t.pos.x * TILESIZE, (t.pos.y * TILESIZE) + TILESIZE - (TILESIZE * t.elevation))

            pygame.draw.polygon(screen, color, [p1, p2, p3])

            render_collision_mesh(screen, "white", t, 3)

    cols = font.render(f"{collisions}", True, "white")
    lcols = font.render(f"{p._last_collision_types}", True, "white")
    s = collisions == p._last_collision_types
    cols_same = font.render(f"{s}", True, "white")
    screen.blit(cols, (0, 0))
    screen.blit(lcols, (0, 20))
    screen.blit(cols_same, (0, 40))

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
