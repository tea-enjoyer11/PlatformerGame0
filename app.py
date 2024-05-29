from typing import Sequence
from enum import Enum, auto
import pygame
import sys
from pygame import Vector2, Surface, Rect, Color
import pygame_gui
import pygame_gui.ui_manager
from typing import Iterable, Hashable, Optional, Callable, Sequence
import random
from Scripts.particles import ParticleGroup, ImageCache, CircleParticle, LeafParticle
from Scripts.utils import load_image, draw_text
from Scripts.utils_math import dist
# from Scripts.opengl_backend_moderngl import Renderer
# from Scripts.opengl_backend import Renderer


RES = Vector2(800, 600)


mainClock = pygame.time.Clock()
pygame.init()
pygame.font.init()
# screen = pygame.display.set_mode(RES, pygame.OPENGL | pygame.DOUBLEBUF)
screen = pygame.display.set_mode(RES, 0, 32)
font = pygame.font.SysFont("arial", 21)

TILESIZE = 32
CHUNKSIZE = 8
CHUNKWIDTH = CHUNKSIZE * TILESIZE


IMGS = [load_image("assets/tile.png"), load_image("assets/ramp_left.png"), load_image("assets/ramp_right.png")]
# IMGS = [load_image("assets/tiles/grass/0.png"), load_image("assets/tiles/grass/3.png"), load_image("assets/tiles/grass/7.png")]
IMGS = {
    0: load_image("assets/tile.png"),
    1: load_image("assets/ramp_left.png"),
    2: load_image("assets/ramp_right.png")
}


class TileType(Enum):
    TILE = auto()
    RAMP_LEFT = auto()
    RAMP_RIGHT = auto()


class Tile:
    __slots__ = ("pos", "type", "img_idx")

    def __init__(self, pos: Vector2, tile_type: TileType = TileType.TILE) -> None:
        if not isinstance(pos, Vector2):
            pos = Vector2(pos)
        self.pos = pos
        self.type = tile_type

        self.img_idx = 0

    # def __repr__(self) -> str:
    #     return f"<{self.pos=}, {self.type=}, {self.img_idx=}>"


class Ramp(Tile):
    __slots__ = ("elevation",)

    def __init__(self, pos: Vector2, tile_type: TileType, elevation: float = 1) -> None:  # angegeben in wie TILESIZE einheit
        super().__init__(pos, tile_type)

        self.elevation = elevation

        if self.type == TileType.RAMP_LEFT:
            self.img_idx = f"LEFT{elevation}"
            if self.img_idx not in IMGS:
                IMGS[self.img_idx] = pygame.transform.scale(IMGS[1], (TILESIZE, TILESIZE * elevation))
        else:
            self.img_idx = f"RIGHT{elevation}"
            if self.img_idx not in IMGS:
                IMGS[self.img_idx] = pygame.transform.scale(IMGS[2], (TILESIZE, TILESIZE * elevation))

    # def __repr__(self) -> str:
    #     return f"<{self.pos=}, {self.type=}, {self.img_idx=}, {self.elevation=}>"


class Chunk:
    __slots__ = ("pos", "size", "_tiles", "_pre_renderd_surf", "_pre_renderd_surf_size", "pre_render_offset")
    default_pre_renderd_surf_size = Vector2(CHUNKSIZE * TILESIZE, CHUNKSIZE * TILESIZE)

    def __init__(self, pos: Vector2, size) -> None:
        self.pos = pos
        self.size = size
        self._tiles: dict[tuple, Tile] = {}

        self._pre_renderd_surf: Surface = None
        self._pre_renderd_surf_size: Vector2 = None
        self.pre_render_offset = Vector2(0)

    def get(self, pos: tuple) -> Tile | None:
        if pos in self._tiles:
            return self._tiles[pos]
        return None

    def get_all(self) -> list[Tile]:
        return list(self._tiles.values())

    def get_in_range(self, pos: Vector2, radius: float) -> list[Tile | Ramp]:

        # !!! ARSCH LANGSAM !!!

        ret: list[Tile | Ramp] = []

        x, y = pos.x // TILESIZE % CHUNKSIZE, pos.y // TILESIZE % CHUNKSIZE

        for _y in range(-radius, radius):
            for _x in range(-radius, radius):
                p = (int(x + _x), int(y + _y))
                if p in self._tiles:
                    ret.append(self._tiles[p])
                    print((x, y), p)

        return ret

    def add(self, tile: Tile) -> None:
        pos = tuple(tile.pos)
        pos = (pos[0] % CHUNKSIZE, pos[1] % CHUNKSIZE)
        # print("         localpos: ", pos)
        self._tiles[pos] = tile

    def adds(self, tiles: list[Tile]) -> None:
        for tile in tiles:
            pos = tuple(tile.pos)
            pos = (pos[0] % CHUNKSIZE, pos[1] % CHUNKSIZE)
            self._tiles[pos] = tile

    def _tile_is_on_edge(self, tile: Tile | Ramp) -> bool:
        x, y = tile.pos.x % CHUNKSIZE, tile.pos.y % CHUNKSIZE
        left_right = (x == 0 or x == self.size[0]) and 0 <= y <= self.size[1]
        top_bottom = (y == 0 or y == self.size[1]) and 0 <= x <= self.size[0]
        if left_right:
            return left_right
        if top_bottom:
            return top_bottom
        return False

    def pre_render(self):
        l = []
        global_tile_offset = Vector2(0)

        # ! Smart approach
        ramps, tiles = [], []
        for _, tile in self._tiles.items():
            if tile.type in [TileType.RAMP_LEFT, TileType.RAMP_RIGHT]:
                ramps.append(tile)
            else:
                tiles.append(tile)

        for ramp in sorted(ramps, key=lambda r: r.elevation, reverse=True):
            on_edge = self._tile_is_on_edge(ramp)
            offset_y = TILESIZE * ramp.elevation - TILESIZE
            local_pos = (ramp.pos.x % CHUNKSIZE, ramp.pos.y % CHUNKSIZE)
            if ramp.elevation > 1 and on_edge:
                if global_tile_offset.y < offset_y:
                    global_tile_offset.y = offset_y
            local_pos = (local_pos[0] * TILESIZE, local_pos[1] * TILESIZE + global_tile_offset.y - offset_y)
            l.append((IMGS[ramp.img_idx], local_pos))

        for tile in tiles:
            local_pos = (tile.pos.x % CHUNKSIZE, tile.pos.y % CHUNKSIZE)
            local_pos = (local_pos[0] * TILESIZE, local_pos[1] * TILESIZE + global_tile_offset.y)
            l.append((IMGS[tile.img_idx], local_pos))

        # ! Naive approach
        # for local_pos, tile in self._tiles.items():
        #     offset = 0
        #     if tile.type in [TileType.RAMP_LEFT, TileType.RAMP_RIGHT]:
        #         offset = TILESIZE * tile.elevation - TILESIZE
        #     local_pos = (local_pos[0] * TILESIZE, local_pos[1] * TILESIZE - offset)
        #     l.append((IMGS[tile.img_idx], local_pos))

        w, h = self.size[0] * TILESIZE, self.size[1] * TILESIZE
        surf = Surface((w + global_tile_offset.x, h + global_tile_offset.y))
        surf.set_colorkey("black")

        surf.fblits(l)

        self._pre_renderd_surf = surf
        self._pre_renderd_surf_size = Vector2(surf.get_size())
        self.pre_render_offset = global_tile_offset

    def get_pre_render(self, offset: Vector2 = Vector2(0)) -> tuple[Surface, tuple]:
        global_pos = tuple(self.pos)
        global_pos = (global_pos[0] * self.size[0] * TILESIZE - offset[0], global_pos[1] * self.size[1] * TILESIZE - offset[1])
        return (self._pre_renderd_surf, global_pos - self.pre_render_offset)


def on_edge_of_chunk(pos: Vector2) -> list[bool]:
    """_summary_
    No need to convert `pos` to a 'Chunk' position. This method does this automatically!

    Args:
        pos (Vector2): position to check

    Returns:
        list[bool]: [on_top_edge, on_right_edge, on_bottom_edge, on_left_edge]
    """
    x, y = pos.x / TILESIZE % CHUNKSIZE, pos.y / TILESIZE % CHUNKSIZE
    # x, y = int(x), int(y)
    # print(x, y)

    edge_radius = 2.5

    top = right = bottom = left = False
    if 0 <= y <= edge_radius:
        top = True
    if CHUNKSIZE - edge_radius <= y <= CHUNKSIZE:
        bottom = True
    if 0 <= x <= edge_radius:
        left = True
    if CHUNKSIZE - edge_radius <= x <= CHUNKSIZE:
        right = True

    return [top, right, bottom, left]


class TileMap:
    __slots__ = ("_chunks", "chunk_size", "amount_of_tiles", "culling_offset")

    def __init__(self, chunk_size=(CHUNKSIZE, CHUNKSIZE)) -> None:
        # self._tiles: dict[tuple, Tile] = {}
        self._chunks: dict[tuple, Chunk] = {}

        self.chunk_size = chunk_size

        self.amount_of_tiles = 0

        self.culling_offset = Vector2(
            RES.x // TILESIZE / 4,
            RES.y // TILESIZE / 4
        )

    def pre_render_chunks(self) -> None:
        [c.pre_render() for c in self._chunks.values()]

    def add(self, tiles: list[Tile]) -> None:
        for tile in tiles:
            # self._tiles[tuple(tile.pos)] = tile

            related_chunk_pos = (tile.pos.x // self.chunk_size[0], tile.pos.y // self.chunk_size[1])
            # print(related_chunk_pos)

            if related_chunk_pos not in self._chunks:
                # chunk_pos = (related_chunk_pos[0] * TILESIZE, related_chunk_pos[1] * TILESIZE)
                self._chunks[related_chunk_pos] = Chunk(related_chunk_pos, size=self.chunk_size)

            chunk = self._chunks[related_chunk_pos]
            chunk.add(tile)
        self.amount_of_tiles += len(tiles)

    def get(self, pos: tuple) -> Tile:
        if not isinstance(pos, tuple):
            try:
                pos = tuple(pos)
            except ValueError:
                print('Value Error in pos conversion. "{pos}" could not be converted to a tuple.')
                pos = None
        if pos in self._tiles:
            return self._tiles[pos]

    def get_around(self, pos: Vector2, range: float) -> list[Tile]:
        related_chunk_pos = Vector2(pos.x // TILESIZE // self.chunk_size[0], pos.y // TILESIZE // self.chunk_size[1])
        # print("related chunk position:", related_chunk_pos, pos)
        ret = []
        neighbors = [Vector2(0.0, 0.0), Vector2(-1.0, 0.0), Vector2(1.0, 0.0), Vector2(0.0, -1.0), Vector2(0.0, 1.0), Vector2(-1, -1), Vector2(1, 1), Vector2(-1, 1), Vector2(1, -1)]

        # ! New approach
        on_edges = on_edge_of_chunk(pos)
        neighbor_positions = [  # Define the relative positions for each possible neighbor
            (0, -1),  # top
            (1, 0),   # right
            (0, 1),   # bottom
            (-1, 0),  # left
            (1, -1),  # top-right
            (1, 1),   # bottom-right
            (-1, 1),  # bottom-left
            (-1, -1)  # top-left
        ]
        neighbor_conditions = [  # Define the conditions for each neighbor based on the `on_edges` list
            (0,),     # top
            (1,),     # right
            (2,),     # bottom
            (3,),     # left
            (0, 1),   # top-right
            (1, 2),   # bottom-right
            (2, 3),   # bottom-left
            (0, 3)    # top-left
        ]
        processed_chunks = set()  # to keep track of processed chunks

        if tuple(related_chunk_pos) in self._chunks:
            ret += self._chunks[tuple(related_chunk_pos)].get_all()

        # Iterate over each possible neighbor and its conditions
        for pos, conditions in zip(neighbor_positions, neighbor_conditions):
            if all(on_edges[c] for c in conditions):  # Check if all conditions are met
                rel_chunk = tuple(related_chunk_pos + Vector2(*pos))
                if rel_chunk not in processed_chunks:  # Check if the chunk has not been processed yet
                    if rel_chunk in self._chunks:
                        ret += self._chunks[rel_chunk].get_all()
                    processed_chunks.add(rel_chunk)  # Mark the chunk as processed

        # ! Old approach
        # for offset in neighbors:
        #     chunk_pos = related_chunk_pos + offset
        #     if tuple(chunk_pos) in self._chunks:
        #         # print(chunk_pos, "is in check radius")
        #         tiles = self._chunks[tuple(chunk_pos)].get_all()
        #         ret += tiles
        return ret

    def get_all(self) -> list[Tile]:
        r = []
        for _, chunk in self._chunks.items():
            r += chunk.get_all()
        return r

    def render(self, surf: Surface, target_pos: Vector2, offset: Vector2 = Vector2(0)) -> None:
        target_pos = (target_pos[0] / TILESIZE // self.chunk_size[0], target_pos[1] / TILESIZE // self.chunk_size[1])

        p1 = (int(target_pos[0] - self.culling_offset.x), int(target_pos[1] - self.culling_offset.x))
        p2 = (int(target_pos[0] + self.culling_offset.y), int(target_pos[1] + self.culling_offset.y))

        l = []
        for y in range(p1[1], p2[1] + 1):
            for x in range(p1[0], p2[0] + 1):
                if (x, y) in self._chunks:
                    l.append(self._chunks[(x, y)].get_pre_render(offset))

        surf.fblits(l)

        for y in range(p1[1], p2[1] + 1):
            for x in range(p1[0], p2[0] + 1):
                if (x, y) in self._chunks:
                    chunk = self._chunks[(x, y)]
                    if chunk._pre_renderd_surf_size != Chunk.default_pre_renderd_surf_size:
                        pygame.draw.rect(surf, "blue", Rect(x * CHUNKWIDTH - offset[0] - chunk.pre_render_offset.x, y * CHUNKWIDTH - offset[1] - chunk.pre_render_offset.y, TILESIZE * CHUNKSIZE + chunk.pre_render_offset.x, TILESIZE * CHUNKSIZE + chunk.pre_render_offset.y), 4)
                    pygame.draw.rect(surf, "red", Rect(x * CHUNKWIDTH - offset[0], y * CHUNKWIDTH - offset[1], TILESIZE * CHUNKSIZE, TILESIZE * CHUNKSIZE), 2)


def collision_test(object_1: Rect, object_list: list[Rect]) -> list[Rect]:
    collision_list = []
    for obj in object_list:
        if obj.colliderect(object_1):
            collision_list.append(obj)
    return collision_list


def tile_rect(t: Tile | Ramp, offset: Vector2 = Vector2(0)) -> Rect:
    if isinstance(t, Ramp):
        x = t.pos.x * TILESIZE - offset.x
        y = (t.pos.y * TILESIZE) + TILESIZE - (TILESIZE * t.elevation) - offset.y
        w = TILESIZE
        h = TILESIZE * t.elevation
        return Rect(x, y, w, h)
    else:  # isinstance(t, Tile)
        return Rect(t.pos.x * TILESIZE - offset.x, t.pos.y * TILESIZE - offset.y, TILESIZE, TILESIZE)


def render_collision_mesh(surf: Surface, color: Color, t: Tile | Ramp, width: int = 1, offset: Vector2 = Vector2(0)) -> None:
    if isinstance(t, Ramp):
        r = tile_rect(t, offset=offset)
        p1, p2 = r.bottomleft, r.topright
        if t.type == TileType.RAMP_LEFT:
            p1, p2 = r.bottomright, r.topleft
        pygame.draw.rect(surf, color, r, width)
        pygame.draw.line(surf, color, p1, p2, width)
    else:  # isinstance(t, Tile)
        r = tile_rect(t, offset=offset)
        pygame.draw.rect(surf, color, r, width)


class Player():
    __slots__ = ("pos", "color", "rect", "vertical_momentum", "min_step_height", "_last_pos", "_collision_types", "_last_collision_types")

    def __init__(self, pos: Vector2):
        self.pos = pos
        self.color = (0, 0, 255)
        self.rect = Rect(pos.x, pos.y, TILESIZE // 2, TILESIZE)
        self.vertical_momentum = 0

        self.min_step_height = .5  # in TILESIZE Größe gerechnet

        self._last_pos = Vector2(0)

        self._collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}
        self._last_collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}

    def _is_steppable(self, tile: Rect):
        top_point = tile.y - tile.height
        # print(top_point - self.pos.y <= self.min_step_height * TILESIZE)
        return top_point - self.pos.y <= self.min_step_height * TILESIZE and self._last_collision_types["bottom"] and (self._last_collision_types["right"] or self._last_collision_types["left"])

    def _is_steppable_ramp(self, ramp: Ramp):
        return TILESIZE * ramp.elevation <= self.min_step_height * TILESIZE

    def move(self, movement: Sequence[float], tiles: list[Tile], dt: float, noclip: bool = False):
        self._last_pos = self.pos.copy()
        self._last_collision_types = self._collision_types.copy()
        collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}

        if noclip:
            self.pos[0] += movement[0] * dt
            self.rect.x = int(self.pos[0])
            self.pos[1] += movement[1] * dt
            self.rect.y = int(self.pos[1])

            self._collision_types = collision_types
            return collision_types

        normal_tiles = [tile_rect(t) for t in tiles if t.type == TileType.TILE]  # make list of all normal tile rects
        ramps: list[Ramp] = [t for t in tiles if t.type in [TileType.RAMP_LEFT, TileType.RAMP_RIGHT]]  # make list of all ramps

        # handle standard collisions
        self.pos[0] += movement[0] * dt
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
            if self._is_steppable(t):  # das funktioniert nur wenn man an der linken kannte des spielers steht, dann auch nur bis dtmultiplier 2.5, ab 3.0 gehts net mehr TODO: FIXEN
                self.rect.bottom = t.top
                collision_types['bottom'] = True
                self.pos[1] = self.rect.y - 1  # kleiner offset, damit der Spieler nicht an der Kante stecken bleibt
        self.pos[1] += movement[1] * dt
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

                steppable = self._is_steppable_ramp(ramp)

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
# tiles: list[Ramp | Tile] = [Tile(Vector2(0, 0)), Ramp('red', Vector2(3, 8), TileType.RAMP_RIGHT), Ramp('red', Vector2(5, 8), TileType.RAMP_RIGHT), Ramp('red', Vector2(7, 8), TileType.RAMP_LEFT, 0.5), Tile('red', Vector2(6, 8)), Tile('red', Vector2(4, 6)), Ramp('red', Vector2(4, 5), TileType.RAMP_LEFT), Tile('red', Vector2(3, 5)), Tile(Vector2(11, 8)), Tile(Vector2(14, 8)), Tile(Vector2(14, 7))]
tiles: list[Ramp | Tile] = [Ramp(Vector2(2, 8), TileType.RAMP_RIGHT, 1), Ramp(Vector2(4, 8), TileType.RAMP_LEFT, 1), Ramp(Vector2(6, 8), TileType.RAMP_RIGHT, 0.5), Ramp(Vector2(8, 8), TileType.RAMP_LEFT, 0.5), Ramp(Vector2(10, 8), TileType.RAMP_RIGHT, 2), Ramp(Vector2(12, 8), TileType.RAMP_LEFT, 2)]
for i in range(16):
    tiles.append(Tile(Vector2(i, 9)))
# tiles = []
tiles.append(Tile(Vector2(0, 0)))
for x in range(-16, 16):
    for y in range(16):
        tiles.append(Tile(Vector2(x, 10 + y)))
p = Player(Vector2(200, 500))

right = False
left = False
up = False
down = False
boost = False
speed = 200
dt_multiplicator = 1
gravity = 2500
max_gravity = 1000
jumpforce = 700
noclip = False
scroll = Vector2(0)
pygame_gui_manager = pygame_gui.ui_manager.UIManager((800, 600))
tile_map = TileMap()
tile_map.add(tiles)
tile_map.pre_render_chunks()

img_cache = ImageCache(load_image)
particle_group = ParticleGroup(img_cache)

# renderer = Renderer()

# region Slider setup
gravity_slider = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(210, 500, 500, 30),
                                                        start_value=gravity,
                                                        value_range=(100, 2500),
                                                        manager=pygame_gui_manager)
gravity_textbox = pygame_gui.elements.ui_text_entry_box.UITextEntryBox(pygame.Rect(110, 500, 90, 30),
                                                                       f"{gravity}",
                                                                       manager=pygame_gui_manager)
gravity_lbl = pygame_gui.elements.ui_label.UILabel(pygame.Rect(10, 500, 90, 30),
                                                   "Gravity",
                                                   pygame_gui_manager)
max_gravity_slider = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(210, 530, 500, 30),
                                                            start_value=max_gravity,
                                                            value_range=(100, 2500),
                                                            manager=pygame_gui_manager)
max_gravity_lbl = pygame_gui.elements.ui_label.UILabel(pygame.Rect(10, 530, 90, 30),
                                                       "Max. Gravity",
                                                       pygame_gui_manager)
max_gravity_textbox = pygame_gui.elements.ui_text_entry_box.UITextEntryBox(pygame.Rect(110, 530, 90, 30),
                                                                           f"{max_gravity}",
                                                                           manager=pygame_gui_manager)
jumpforce_slider = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(210, 560, 500, 30),
                                                          start_value=jumpforce,
                                                          value_range=(100, 2500),
                                                          manager=pygame_gui_manager)
jumpforce_textbox = pygame_gui.elements.ui_text_entry_box.UITextEntryBox(pygame.Rect(110, 560, 90, 30),
                                                                         f"{jumpforce}",
                                                                         manager=pygame_gui_manager)
jumpforce_lbl = pygame_gui.elements.ui_label.UILabel(pygame.Rect(10, 560, 90, 30),
                                                     "Jumpforce",
                                                     pygame_gui_manager)
# endregion

# Loop ------------------------------------------------------- #
run = True
while run:
    dt = mainClock.tick(0) * 0.001
    dt *= dt_multiplicator

    # self.scroll += ((self.player.pos - Vector2(4, 4)) - RES / 4 / 2 - self.scroll) / 30
    scroll += ((p.pos - Vector2(TILESIZE / 2)) - RES / 2 - scroll) / 30

    # Background --------------------------------------------- #
    screen.fill((0, 0, 0))

    # Player ------------------------------------------------- #
    if not noclip:
        p.vertical_momentum += gravity * dt
        p.vertical_momentum = min(p.vertical_momentum, max_gravity)
        player_movement = [0, p.vertical_momentum]
    if noclip:
        player_movement = [0, 0]

    if right:
        player_movement[0] += speed
    if left:
        player_movement[0] -= speed
    if noclip:
        if up:
            player_movement[1] -= speed
        if down:
            player_movement[1] += speed

    if boost:
        player_movement[0] *= 4
        player_movement[1] *= 4

    close_tiles = tile_map.get_around(p.pos, 5)
    collisions = p.move(player_movement, close_tiles, dt, noclip)
    if (collisions['bottom']) or (collisions['top']) and not noclip:
        p.vertical_momentum = 0

    tile_map.render(screen, p.pos, offset=scroll)
    pygame.draw.rect(screen, p.color, Rect(Vector2(p.rect.topleft) - scroll, p.rect.size))

    for tile in close_tiles:
        render_collision_mesh(screen, "yellow", tile, offset=scroll)

    draw_text(screen, f"DT:{dt:.4f} DT multiplier:{dt_multiplicator:.4f}", (0, 80))
    draw_text(screen, f"{mainClock.get_fps():.0f}", (500, 0))
    draw_text(screen, f"POS:{p.pos} NOCLIP: {noclip}", (500, 50))
    draw_text(screen, f"TILEMAP:\nAmount of Chunks: {len(tile_map._chunks)}\nAmount of Tiles: {tile_map.amount_of_tiles}", (500, 100))
    draw_text(screen, f"PARTICLES:\nAmount of Particles: {len(particle_group)}", (500, 200))
    draw_text(screen, f"{collisions}", (0, 0), font=font)
    draw_text(screen, f"{p._last_collision_types}", (0, 20))
    draw_text(screen, f"Are the last and current collisions the same: {collisions == p._last_collision_types}", (0, 40))

    # Buttons ------------------------------------------------ #
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                right = True
            if event.key == pygame.K_a:
                left = True
            if event.key == pygame.K_w:
                up = True
            if event.key == pygame.K_s:
                down = True
            if event.key == pygame.K_SPACE:
                p.vertical_momentum = -jumpforce
            if event.key == pygame.K_TAB:
                noclip = not noclip
                p.vertical_momentum = 0
            if event.key == pygame.K_UP:
                dt_multiplicator = min(5, dt_multiplicator + 0.5)
            if event.key == pygame.K_DOWN:
                dt_multiplicator = max(0, dt_multiplicator - 0.5)
            if event.key == pygame.K_r:
                p.pos = Vector2(200, 50)
                p.vertical_momentum = 0
                particle_group.clear()
            if event.key == pygame.K_LCTRL:
                boost = True
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_d:
                right = False
            if event.key == pygame.K_a:
                left = False
            if event.key == pygame.K_w:
                up = False
            if event.key == pygame.K_s:
                down = False
            if event.key == pygame.K_LCTRL:
                boost = False

        # region ui events
        if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if event.ui_element == gravity_slider:
                print('current slider value:', event.value)
                gravity_textbox.set_text(str(event.value))
                gravity = event.value
            elif event.ui_element == max_gravity_slider:
                print('current slider value:', event.value)
                max_gravity_textbox.set_text(str(event.value))
                max_gravity = event.value
            elif event.ui_element == jumpforce_slider:
                print('current slider value:', event.value)
                jumpforce_textbox.set_text(str(event.value))
                jumpforce = event.value

        if event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            if event.ui_element == gravity_textbox:
                print("Changed text:", event.text)
                val = gravity_slider.get_current_value()
                try:
                    val = max(100, min(int(event.text), 1000))
                except ValueError:
                    print(f"Converting error: {event.text=}")
                gravity_slider.set_current_value(val)
                gravity = val
            elif event.ui_element == max_gravity_textbox:
                print("Changed text:", event.text)
                val = max_gravity_slider.get_current_value()
                try:
                    val = max(100, min(int(event.text), 1000))
                except ValueError:
                    print(f"Converting error: {event.text=}")
                max_gravity_slider.set_current_value(val)
                max_gravity = val
            elif event.ui_element == jumpforce_textbox:
                print("Changed text:", event.text)
                val = jumpforce_slider.get_current_value()
                try:
                    val = int(event.text)
                except ValueError:
                    print(f"Converting error: {event.text=}")
                jumpforce_slider.set_current_value(val)
                jumpforce = val
        # endregion

        pygame_gui_manager.process_events(event)

    m_pos = tuple(pygame.Vector2(pygame.mouse.get_pos()))
    if pygame.mouse.get_pressed()[0]:
        particle_group.add([CircleParticle(m_pos, (random.randrange(-100, 100), random.randrange(-100, 100)), 4, type="particle") for _ in range(5)])
    if pygame.mouse.get_pressed()[2]:
        particle_group.add([LeafParticle(m_pos, (random.randrange(-30, 30), random.randrange(-30, 30)), 18, type="leaf") for _ in range(5)])

    particle_group.update(dt)
    particle_group.draw(screen, blend=pygame.BLEND_RGB_ADD)

    pygame_gui_manager.update(dt)
    pygame_gui_manager.draw_ui(screen)

    # Update ------------------------------------------------- #
    # renderer.render(screen)
    # renderer.render_particles(particle_group.particles)
    pygame.display.flip()
# renderer.quit()
pygame.quit()
sys.exit()
