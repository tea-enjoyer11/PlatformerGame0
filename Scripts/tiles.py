from copy import deepcopy
from itertools import chain
import os
from Scripts.CONFIG import *
from typing import Literal, Any, List, Dict, Tuple, List
import math
from Scripts.utils_math import clamp_number_to_range_steps


class Queue:
    def __init__(self) -> None:
        self._content: List[object] = []

    def empty(self) -> bool:  # True if empty
        return bool(len(self._content))

    def put(self, obj: object) -> None:
        if obj not in self._content:
            self._content.append(obj)

    def get(self) -> object:
        if self.empty():
            return self._content.pop(0)
        return None

    def __len__(self) -> int:
        return len(self._content)


NEIGHBOR_OFFSETS = [
    (-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)
]
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


class TileType(Enum):
    TILE = auto()
    TILE_CUSTOM = auto()
    RAMP_LEFT = auto()
    RAMP_RIGHT = auto()
    RAMP_CUSTOM = auto()
    ORIENTATION_LEFT = auto()
    ORIENTATION_RIGHT = auto()
    GRASS_BLADE = auto()
    GRASS_PATCH = auto()  # viele blades in einem tile


class Tile:
    __slots__ = ("pos", "type", "img_idx", "size")

    def __init__(self, pos: Vector2, tile_type: TileType = TileType.TILE, img_idx: Any = None) -> None:
        if not isinstance(pos, Vector2):
            pos = Vector2(pos)
        self.pos = pos
        self.type = tile_type

        self.size = (TILESIZE, TILESIZE)

        self.img_idx = 0
        if img_idx:
            self.img_idx = img_idx

    def __repr__(self) -> str:
        return f"<{self.pos=}, {self.type=}, {self.img_idx=}>"


class CustomTile(Tile):
    __slots__ = ("height_data_idx", )

    def __init__(self, pos: Vector2, height_data_idx: Any, img_idx: Any,
                 tile_type: TileType = TileType.TILE_CUSTOM) -> None:
        super().__init__(pos, tile_type)

        self.height_data_idx: Any = height_data_idx
        self.img_idx = img_idx


class Ramp(Tile):
    __slots__ = ("elevation", )

    def __init__(self, pos: Vector2, tile_type: TileType, elevation: float = 1) -> None:  # angegeben in wie TILESIZE einheit
        super().__init__(pos, tile_type)

        self.elevation = elevation
        self.size = (TILESIZE, TILESIZE * elevation)

        if self.type == TileType.RAMP_LEFT:
            self.img_idx = f"LEFT{elevation}"
            if self.img_idx not in IMGS:
                IMGS[self.img_idx] = pygame.transform.scale(IMGS[1], (TILESIZE, TILESIZE * elevation))
        else:
            self.img_idx = f"RIGHT{elevation}"
            if self.img_idx not in IMGS:
                IMGS[self.img_idx] = pygame.transform.scale(IMGS[2], (TILESIZE, TILESIZE * elevation))

    def __repr__(self) -> str:
        return f"<{self.pos=}, {self.type=}, {self.img_idx=}, {self.elevation=}>"


class CustomRamp(Tile):
    __slots__ = ("height_data", "orientation", "size")

    def __init__(self, pos: Vector2, hitbox: Surface, orientation: Literal[TileType.RAMP_LEFT, TileType.RAMP_RIGHT], tile_type: TileType = TileType.RAMP_CUSTOM, img_idx=0) -> None:
        super().__init__(pos, tile_type)

        self.height_data = CustomRamp.parse_data(hitbox)
        self.orientation = orientation
        self.img_idx = img_idx
        self.size = Vector2(hitbox.get_size())

    @staticmethod
    def parse_data(hitbox: Surface) -> Dict[int, int]:
        ret: Dict[int, int] = {}
        # ret ist ein dict wo, die x position als key
        # und die höhe der ramp an der x position als value gespeichert wird
        # Bsp: {1: 2, 2: 3, 3: 5, ...}
        # Dann ist beim ersten pixel die Rampe 2 hoch,
        # beim zweiten 3, beim dritten 5.

        w, h = hitbox.get_size()
        white = Color(255, 255, 255, 255)
        black = Color(0, 0, 0, 255)
        for x in range(w):
            v = 0
            for y in range(h):
                y = h - y - 1
                col = hitbox.get_at((x, y))
                # print((x, y), col)
                if col == white:
                    v += 1
                elif col == black:
                    break
            ret[x] = v
        # print(ret)
        return ret

    def __repr__(self) -> str:
        return f"<{self.pos=}, {self.type=}, {self.img_idx=}, {self.size=}>"


class GrassBlade(Tile):  # representiert nur einen grashalm
    img_cache: Dict[str, Surface] = {}
    offset_cache: Dict[str, Vector2] = {}
    img_half_size_cache: Dict[str, Tuple] = {}
    def rot_function(x) -> float: return 35 * math.sin(0.5 * x)
    max_rotations = 20
    rotation_angle = 35

    def __init__(self, pos: Vector2, img_idx: Any, tile_type: TileType = TileType.GRASS_BLADE) -> None:
        super().__init__(pos, tile_type, img_idx)

        self.base_img_idx = self.img_idx
        self.rot = .0
        self.offset = (0, 0)
        self.update(0)
        self.center_blit_offset = Vector2(GrassBlade.img_cache[f"{self.base_img_idx};0"].get_size()) / 2

    def update(self, time: float) -> None: self.rotate(time)

    def rotate(self, time: float) -> None:

        # ! Idee: die rotations limitieren. Nur von -20 zu 20 in 4er steps. -> nur 10 rotation states

        self.rot = GrassBlade.rot_function(self.pos.x + time)
        self.rot = clamp_number_to_range_steps(self.rot, -GrassBlade.rotation_angle, GrassBlade.rotation_angle, GrassBlade.rotation_angle * 2 / GrassBlade.max_rotations)

        self.img_idx = f"{self.base_img_idx};{int(self.rot)}"

        if self.img_idx not in GrassBlade.img_cache:
            base_idx = f"{self.base_img_idx};0"
            s = pygame.transform.rotate(GrassBlade.img_cache[base_idx], self.rot)
            GrassBlade.img_cache[self.img_idx] = s
            offset = Vector2(s.get_size()) / 2 - GrassBlade.offset_cache[base_idx] / 2
            GrassBlade.offset_cache[self.img_idx] = offset
            GrassBlade.img_half_size_cache[self.img_idx] = tuple(Vector2(s.get_size()) // 2)


class GrassPatch(Tile):  # representiert alle Grashalme in einem tile
    def __init__(self, pos: Vector2, tile_type: TileType = TileType.GRASS_PATCH) -> None:
        super().__init__(pos, tile_type, img_idx=None)


class Chunk:
    __slots__ = ("parent", "pos", "size", "_tiles", "_ghost_tiles", "_pre_renderd_surf",
                 "_pre_renderd_surf_size", "pre_render_offset",
                 "_last_pre_render_data", "_pre_render_data",
                 "_tiles_offgrid")
    default_pre_renderd_surf_size = Vector2(CHUNKSIZE * TILESIZE, CHUNKSIZE * TILESIZE)

    def __init__(self, parent: "TileMap", pos: Vector2, size) -> None:
        self.parent = parent
        self.pos = Vector2(pos)
        self.size = size
        self._tiles: Dict[Tuple, Tile] = {}
        self._tiles_offgrid: Dict[Tuple, Tile] = {}
        self._ghost_tiles: Dict[Tuple, Tile] = {}

        self._pre_renderd_surf: Surface = None
        self._pre_renderd_surf_size: Vector2 = None
        self.pre_render_offset = Vector2(0)
        self._last_pre_render_data = ...  # sollte unterschiedlich zu "_pre_render_data" sein
        self._pre_render_data = None

    def copy(self) -> "Chunk":
        return deepcopy(self)

    def get(self, pos: Tuple) -> Tile | None:
        if pos in self._tiles:
            return self._tiles[pos]
        return None

    def get_all(self) -> List[Tile]:
        return list(self._tiles.values())

    def get_all_offgrid(self) -> List[Tile]:
        return list(self._tiles_offgrid.values())

    def get_around(self, pos: Vector2, size: Vector2 | None = None) -> List[Tile | Ramp]:
        ret: List[Tile | Ramp] = []

        x, y = pos.x // TILESIZE, pos.y // TILESIZE
        x, y = x % CHUNKSIZE, y % CHUNKSIZE
        chunk_global_pos = self.pos * CHUNKWIDTH
        if pos.x < chunk_global_pos.x:
            ...  # pos ist links vom chunk
            x = 0
        elif pos.x > chunk_global_pos.x + CHUNKWIDTH:
            x = CHUNKSIZE - 1
            ...  # pos ist rechts vom chunk
        if pos.y < chunk_global_pos.y:
            ...  # pos ist über chunk
            y = 0
        elif pos.y > chunk_global_pos.y + CHUNKWIDTH:
            y = CHUNKSIZE - 1
            ...  # pos ist unter chunk

        en_size = Vector2(1, 1)
        if size:
            en_size += Vector2(size.x // TILESIZE, size.y // TILESIZE)

        # print(en_size)
        x_off = 0  # -int(en_size.x // 2)
        y_off = 0  # -int(en_size.y // 2)
        for x__ in range(int(en_size[0])):
            for y__ in range(int(en_size[1])):
                for x_, y_ in NEIGHBOR_OFFSETS:
                    p = (x_off + x + x_ + x__, y_off + y + y_ + y__)
                    if p in self._tiles:
                        ret.append(self._tiles[p])
                    if p in self._ghost_tiles:
                        ret.append(self._ghost_tiles[p])

        # x, y = pos.x // TILESIZE % CHUNKSIZE, pos.y // TILESIZE % CHUNKSIZE
        # for x_, y_ in NEIGHBOR_OFFSETS:
        #     p = (x+x_, y+y_)
        #     if p in self._tiles:
        #         ret.append(self._tiles[p])

        return ret

    def is_empty(self) -> bool:
        return len(self._tiles) + len(self._tiles_offgrid)

    def remove(self, pos: Vector2) -> None:
        self._last_pre_render_data = self._calc_pre_render_data()
        ret = False
        pos = (pos[0] % CHUNKSIZE, pos[1] % CHUNKSIZE)
        if pos in self._tiles:
            del self._tiles[pos]
            self.parent.add_to_pre_render_queue(self)
            ret = True
            self._pre_render_data = self._calc_pre_render_data()
        return ret

    def add(self, tile: Tile) -> bool:
        self._last_pre_render_data = self._calc_pre_render_data()
        ret = False
        pos = tuple(tile.pos)
        pos = (pos[0] % CHUNKSIZE, pos[1] % CHUNKSIZE)
        if pos not in self._tiles:
            ret = True
        self._tiles[pos] = tile

        on_edge = self._tile_is_on_edge(tile)
        if sum(on_edge):
            exceeding_chunk_border = tile.size[1] > TILESIZE
            if not exceeding_chunk_border:
                return
            # print(tile.size[1] > TILESIZE, tile)

            # Iterate over each possible neighbor and its conditions
            for pos_, conditions in zip(neighbor_positions, neighbor_conditions):
                if all(on_edge[c] for c in conditions):  # Check if all conditions are met
                    rel_chunk_pos = tuple(self.pos + Vector2(pos_))
                    self.parent._create_empty_chunk(rel_chunk_pos)
                    rel_chunk = self.parent.get_chunk(rel_chunk_pos)
                    for i in range(int(tile.size[1] / TILESIZE)):
                        ghost_pos = tile.pos - Vector2(0, i)
                        if ghost_pos[1] < self.pos.y * CHUNKSIZE:
                            rel_chunk.add_ghost_tile(tile, ghost_pos)
                            self.parent.add_to_pre_render_queue(rel_chunk)
        self._pre_render_data = self._calc_pre_render_data()
        return ret

    def add_offgrid(self, tile: Tile) -> bool:
        ret = True
        pos = tuple(tile.pos)
        if pos in self._tiles_offgrid:
            ret = False
        self._tiles_offgrid[pos] = tile
        return ret

    def remove_offgrid(self, position: Vector2) -> bool:
        ret = False
        pos = tuple(position)
        if pos in self._tiles_offgrid:
            del self._tiles_offgrid[pos]
            ret = True
            self._pre_render_data = self._calc_pre_render_data()
        return ret

    def extend(self, tiles: List[Tile]) -> None:
        self._last_pre_render_data = self._calc_pre_render_data()
        for tile in tiles:
            pos = tuple(tile.pos)
            pos = (pos[0] % CHUNKSIZE, pos[1] % CHUNKSIZE)
            self._tiles[pos] = tile
        self._pre_render_data = self._calc_pre_render_data()

    def _calc_pre_render_data(self) -> List[Iterable]:
        return list(chain(self._tiles.items(), self._ghost_tiles.items()))

    def pre_render_needed(self) -> bool:
        return not hash(self._last_pre_render_data) == hash(self._pre_render_data)

    def add_ghost_tile(self, tile: Tile, pos: Vector2, raw_pos: bool = False):
        pos_ = None
        if raw_pos:
            self._ghost_tiles[tuple(pos)] = tile
        else:
            pos_ = (pos[0] % CHUNKSIZE, pos[1] % CHUNKSIZE)
            self._ghost_tiles[pos_] = tile
        # print("Added Ghost tile", pos_, pos, tile)

    def _tile_is_on_edge(self, tile: Tile | Ramp) -> bool:
        """
        returns:
            List[bool]: [on_top_edge, on_right_edge, on_bottom_edge, on_left_edge]
        """
        x, y = tile.pos.x % CHUNKSIZE, tile.pos.y % CHUNKSIZE
        x = min(self.size[0], x)
        y = max(0, y)

        # if isinstance(tile, CustomRamp) or isinstance(tile, Ramp):
        #     print(additional_w, additional_h, x, y, type(tile))

        on_top_edge = (0 <= x <= self.size[0] and y == 0)
        on_right_edge = (x == self.size[0] and 0 <= y <= self.size[1])
        on_bottom_edge = (0 <= x <= self.size[0] and y == self.size[1])
        on_left_edge = (x == 0 and 0 <= y <= self.size[1])
        # left_right = (x == 0 or x == self.size[0]) and 0 <= y <= self.size[1]
        # top_bottom = (y == 0 or y == self.size[1]) and 0 <= x <= self.size[0]
        # if left_right:
        #     return left_right
        # if top_bottom:
        #     return top_bottom
        return [on_top_edge, on_right_edge, on_bottom_edge, on_left_edge]

    def pre_render(self):
        # if not self.pre_render_needed():
        #     return

        l = []
        global_tile_offset = Vector2(0)

        ramps: List[Ramp] = []
        custom_ramps: List[CustomRamp] = []
        tiles: List[Tile] = []
        custom_tiles: List[CustomTile] = []
        grass_blades: List[GrassBlade] = []

        for _, tile in self._tiles.items():
            if tile.type in [TileType.RAMP_LEFT, TileType.RAMP_RIGHT]:
                ramps.append(tile)
            elif tile.type == TileType.RAMP_CUSTOM:
                custom_ramps.append(tile)
            elif tile.type == TileType.TILE_CUSTOM:
                custom_tiles.append(tile)
            elif tile.type == TileType.GRASS_BLADE:
                grass_blades.append(tile)
            else:
                tiles.append(tile)

        for _, tile in self._tiles_offgrid.items():  # muss eigentlich oben eingebaut werden.
            if tile.type == TileType.GRASS_BLADE:
                grass_blades.append(tile)

        for c_ramp in sorted(custom_ramps, key=lambda r: r.size.y, reverse=True):
            on_edge = self._tile_is_on_edge(c_ramp)
            if sum(on_edge) and c_ramp.size.y > TILESIZE:
                global_tile_offset.y = c_ramp.size.y

        for ramp in sorted(ramps, key=lambda r: r.elevation, reverse=True):
            on_edge = self._tile_is_on_edge(ramp)
            offset_y = TILESIZE * ramp.elevation - TILESIZE
            local_pos = (ramp.pos.x % CHUNKSIZE, ramp.pos.y % CHUNKSIZE)
            if ramp.elevation > 1 and sum(on_edge):
                if global_tile_offset.y < offset_y:
                    global_tile_offset.y = offset_y
            local_pos = (local_pos[0] * TILESIZE, local_pos[1] * TILESIZE + global_tile_offset.y - offset_y)
            l.append((IMGS[ramp.img_idx], local_pos))

        for tile in tiles:
            local_pos = (tile.pos.x % CHUNKSIZE, tile.pos.y % CHUNKSIZE)
            local_pos = (local_pos[0] * TILESIZE, local_pos[1] * TILESIZE + global_tile_offset.y)
            l.append((IMGS[tile.img_idx], local_pos))

        for c_tile in custom_tiles:
            local_pos = (c_tile.pos.x % CHUNKSIZE, c_tile.pos.y % CHUNKSIZE)
            local_pos = (local_pos[0] * TILESIZE, local_pos[1] * TILESIZE + global_tile_offset.y)
            l.append((IMGS[c_tile.img_idx], local_pos))
            # print(IMGS[c_tile.img_idx])

        for c_ramp in custom_ramps:
            local_pos = (c_ramp.pos.x % CHUNKSIZE, c_ramp.pos.y % CHUNKSIZE)
            offset_y = c_ramp.size.y - TILESIZE
            local_pos = (local_pos[0] * TILESIZE, local_pos[1] * TILESIZE + global_tile_offset.y - offset_y)
            l.append((IMGS[c_ramp.img_idx], local_pos))
            # print(local_pos)

        for blade in grass_blades:
            local_pos = (blade.pos.x % CHUNKSIZE, blade.pos.y % CHUNKSIZE)
            local_pos = (local_pos[0] * TILESIZE, local_pos[1] * TILESIZE + global_tile_offset.y)

            local_pos = (local_pos[0] - blade.center_blit_offset.x, local_pos[1] - blade.center_blit_offset.x)

            local_offset = GrassBlade.offset_cache[blade.img_idx]
            if local_offset.y == 0:
                local_offset.y = GrassBlade.img_half_size_cache[blade.img_idx][1] / 1.6
            # print(local_offset, blade.img_idx)
            if local_offset.x < 0:
                local_offset.x *= -2
            local_pos = (local_pos[0] - local_offset[0], local_pos[1] - local_offset[1])

            # local_pos = (local_pos[0] + GrassBlade.img_half_size_cache[blade.img_idx][0], local_pos[1] + GrassBlade.img_half_size_cache[blade.img_idx][1])

            l.append((GrassBlade.img_cache[blade.img_idx], local_pos))

        w, h = self.size[0] * TILESIZE, self.size[1] * TILESIZE
        surf = Surface((w + global_tile_offset.x, h + global_tile_offset.y))
        surf.set_colorkey("black")

        # print(l)
        surf.fblits(l)

        self._pre_renderd_surf = surf
        self._pre_renderd_surf_size = Vector2(surf.get_size())
        self.pre_render_offset = global_tile_offset

    def get_pre_render(self, offset: Vector2 = Vector2(0)) -> tuple[Surface, tuple]:
        global_pos = tuple(self.pos)
        global_pos = (global_pos[0] * self.size[0] * TILESIZE - offset[0], global_pos[1] * self.size[1] * TILESIZE - offset[1])
        # print(self._pre_renderd_surf)
        return (self._pre_renderd_surf, global_pos - self.pre_render_offset)


def on_edge_of_chunk(pos: Vector2) -> List[bool]:
    """_summary_
    No need to convert `pos` to a 'Chunk' position. This method does this automatically!

    Args:
        pos (Vector2): position to check

    Returns:
        List[bool]: [on_top_edge, on_right_edge, on_bottom_edge, on_left_edge]
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
    __slots__ = ("_chunks", "chunk_size", "amount_of_tiles", "amount_of_tiles_offgrid",
                 "amount_of_chunks", "culling_offset", "_pre_render_queue")

    def __init__(self, chunk_size=(CHUNKSIZE, CHUNKSIZE)) -> None:
        # self._tiles: Dict[Tuple, Tile] = {}
        self._chunks: Dict[Tuple, Chunk] = {}

        self.chunk_size: Tuple[int, int] = chunk_size

        self.amount_of_tiles = 0
        self.amount_of_tiles_offgrid = 0
        self.amount_of_chunks = 0
        self._pre_render_queue: Queue[Chunk] = Queue()

        self.culling_offset = Vector2(
            RES.x // TILESIZE / 5,
            RES.y // TILESIZE / 5
        )

    def pre_render_chunks(self) -> None:
        # TODO einen weg finden nur zu prerendern, falls sich was verändert hat. vllt hash von _tiles in _chunks nehmen und das vergleichen?
        # Chunk.pre_render_needed() ist eine Idee, funktioniert in der Praxis aber nicht gut.
        # vllt kann man eine Liste oder Queue haben, wo man die Chunks, die neu sind und noch nicht geprerenderd wurden
        # reinpackt und erst entfernt, wenn diese Funktion durch diese Liste durchgegangen ist.

        # New approach
        # print(len(self._pre_render_queue))
        while self._pre_render_queue.empty():
            c = self._pre_render_queue.get()
            # print(22222, c)
            c.pre_render()

        # Old approach
        # [c.pre_render() for c in self._chunks.values()]  # if c.pre_render_needed()]

    def remove(self, pos: Vector2) -> None:
        related_chunk_pos = (pos.x // self.chunk_size[0], pos.y // self.chunk_size[1])
        if related_chunk_pos in self._chunks:
            chunk = self._chunks[related_chunk_pos]
            if chunk.remove(pos):
                self.amount_of_tiles -= 1
                self.add_to_pre_render_queue(chunk)  # TODO checken ob das keinen fehler aufwirft, weil der chunk später auch entfernt werden kann!
            if not self._chunks[related_chunk_pos].is_empty():
                del self._chunks[related_chunk_pos]
                self.amount_of_chunks -= 1

    def remove_offgrid(self, pos: Vector2) -> None:
        related_chunk_pos = (pos.x // self.chunk_size[0], pos.y // self.chunk_size[1])
        if related_chunk_pos in self._chunks:
            chunk = self._chunks[related_chunk_pos]
            if chunk.remove_offgrid(pos):
                self.amount_of_tiles_offgrid -= 1
                self.add_to_pre_render_queue(chunk)  # TODO checken ob das keinen fehler aufwirft, weil der chunk später auch entfernt werden kann!
            if not self._chunks[related_chunk_pos].is_empty():
                del self._chunks[related_chunk_pos]
                self.amount_of_chunks -= 1

    def add_to_pre_render_queue(self, chunk: Chunk) -> None:
        self._pre_render_queue.put(chunk)

    def add(self, tile: Tile) -> None:
        related_chunk_pos = (tile.pos.x // self.chunk_size[0], tile.pos.y // self.chunk_size[1])

        if related_chunk_pos not in self._chunks:
            # chunk_pos = (related_chunk_pos[0] * TILESIZE, related_chunk_pos[1] * TILESIZE)
            c = Chunk(self, related_chunk_pos, size=self.chunk_size)
            self._chunks[related_chunk_pos] = c
            self.amount_of_chunks += 1
            self.add_to_pre_render_queue(c)

        chunk = self._chunks[related_chunk_pos]
        if chunk.add(tile):
            self.amount_of_tiles += 1
            self.add_to_pre_render_queue(chunk)

    def add_offgrid(self, tile: Tile) -> None:
        related_chunk_pos = (tile.pos.x // self.chunk_size[0], tile.pos.y // self.chunk_size[1])

        if related_chunk_pos not in self._chunks:
            # chunk_pos = (related_chunk_pos[0] * TILESIZE, related_chunk_pos[1] * TILESIZE)
            c = Chunk(self, related_chunk_pos, size=self.chunk_size)
            self._chunks[related_chunk_pos] = c
            self.amount_of_chunks += 1

        chunk = self._chunks[related_chunk_pos]
        if chunk.add_offgrid(tile):
            self.amount_of_tiles_offgrid += 1
        self.add_to_pre_render_queue(chunk)

    def extend(self, tiles: List[Tile]) -> None:
        for tile in tiles:
            # self._tiles[tuple(tile.pos)] = tile

            related_chunk_pos = (tile.pos.x // self.chunk_size[0], tile.pos.y // self.chunk_size[1])
            # print(related_chunk_pos)

            if related_chunk_pos not in self._chunks:
                # chunk_pos = (related_chunk_pos[0] * TILESIZE, related_chunk_pos[1] * TILESIZE)
                self._chunks[related_chunk_pos] = Chunk(self, related_chunk_pos, size=self.chunk_size)

            chunk = self._chunks[related_chunk_pos]
            if chunk.add(tile):
                self.amount_of_tiles += 1
                self.add_to_pre_render_queue(chunk)

    def get(self, pos: Tuple) -> Tile:
        if not isinstance(pos, tuple):
            try:
                pos = tuple(pos)
            except ValueError:
                print('Value Error in pos conversion. "{pos}" could not be converted to a tuple.')
                pos = None
        if pos in self._tiles:
            return self._tiles[pos]

    def get_chunk(self, pos: Tuple) -> Chunk | None:
        if pos in self._chunks:
            return self._chunks[pos]
        return None

    def _create_empty_chunk(self, pos: Tuple) -> Chunk | None:
        if pos not in self._chunks:
            c = Chunk(self, pos, self.chunk_size)
            self._chunks[pos] = c
            return c
        return None

    def get_around(self, pos: Vector2) -> List[Tile]:
        related_chunk_pos = Vector2(pos.x // TILESIZE // self.chunk_size[0], pos.y // TILESIZE // self.chunk_size[1])
        # print("related chunk position:", related_chunk_pos, pos)
        ret = []

        pos_on_edge = on_edge_of_chunk(pos)

        processed_chunks = set()  # to keep track of processed chunks

        if tuple(related_chunk_pos) in self._chunks:
            ret += self._chunks[tuple(related_chunk_pos)].get_around(pos)  # , size=Vector2(TILESIZE * 2, TILESIZE * 2))

        # Iterate over each possible neighbor and its conditions
        for pos_, conditions in zip(neighbor_positions, neighbor_conditions):
            if all(pos_on_edge[c] for c in conditions):  # Check if all conditions are met
                rel_chunk = tuple(related_chunk_pos + Vector2(*pos_))
                if rel_chunk not in processed_chunks:  # Check if chunk has not been processed
                    if rel_chunk in self._chunks:
                        ret += self._chunks[rel_chunk].get_around(pos)
                    processed_chunks.add(rel_chunk)  # Mark chunk as processed

        return ret

    def get_all(self) -> List[Tile]:
        r = []
        for _, chunk in self._chunks.items():
            r += chunk.get_all()
        return r

    def get_all_offgrid(self) -> List[Tile]:
        r = []
        for _, chunk in self._chunks.items():
            rr = chunk.get_all_offgrid()
            if rr:
                self.add_to_pre_render_queue(chunk)
                r += rr
        return r

    def render(self, surf: Surface, target_pos: Vector2, offset: Vector2 = Vector2(0)) -> None:
        target_pos = (target_pos[0] / TILESIZE // self.chunk_size[0], target_pos[1] / TILESIZE // self.chunk_size[1])

        p1 = (
            int(target_pos[0] - self.culling_offset.x),
            int(target_pos[1] - self.culling_offset.y)
        )
        p2 = (
            int(target_pos[0] + self.culling_offset.x),
            int(target_pos[1] + self.culling_offset.y)
        )
        # print(p1, p2)

        l = []
        for y in range(p1[1], p2[1] + 1):
            for x in range(p1[0], p2[0] + 1):
                if (x, y) in self._chunks:
                    l.append(self._chunks[(x, y)].get_pre_render(offset))

        # print(l)
        surf.fblits(l)

        for y in range(p1[1], p2[1] + 1):
            for x in range(p1[0], p2[0] + 1):
                if (x, y) in self._chunks:
                    chunk = self._chunks[(x, y)]
                    if chunk._pre_renderd_surf_size != Chunk.default_pre_renderd_surf_size:
                        pygame.draw.rect(surf, "blue", Rect(x * CHUNKWIDTH - offset[0] - chunk.pre_render_offset.x, y * CHUNKWIDTH - offset[1] - chunk.pre_render_offset.y, TILESIZE * CHUNKSIZE + chunk.pre_render_offset.x, TILESIZE * CHUNKSIZE + chunk.pre_render_offset.y), 4)
                    pygame.draw.rect(surf, "red", Rect(x * CHUNKWIDTH - offset[0], y * CHUNKWIDTH - offset[1], TILESIZE * CHUNKSIZE, TILESIZE * CHUNKSIZE), 2)

    def serialize(self, directory: str) -> None:
        for chunk in self._chunks.values():
            serialize_chunk(chunk.copy(), directory)

    @ staticmethod
    def deserialize(directory: str) -> "TileMap":
        # load ...
        chunks: Dict[Tuple, Chunk] = {}
        tilemap = TileMap()

        files = [f for f in os.listdir(directory) if f.endswith(".data")]
        # print(files)
        for file_path in files:
            c: Chunk = None
            with open(f"{directory}/{file_path}", "rb") as f:
                data = f.read()
                c = load_compressed_pickle(data)
            if c:
                c.parent = tilemap
            chunks[tuple(c.pos)] = c
            # print(c._tiles)

            if not hasattr(c, "_tiles_offgrid"):
                setattr(c, "_tiles_offgrid", {})
            else:
                if isinstance(c._tiles_offgrid, list):
                    c._tiles_offgrid = {}
        tilemap._chunks = chunks
        print(000000, chunks)
        [tilemap.add_to_pre_render_queue(c) for c in chunks.values()]
        tilemap.pre_render_chunks()
        return tilemap


def collision_test(object_1: Rect, object_list: List[Rect]) -> List[Rect]:
    collision_list = []
    for obj in object_list:
        if obj.colliderect(object_1):
            collision_list.append(obj)
    return collision_list


def tile_rect(t: Tile | Ramp, offset: Vector2 = Vector2(0)) -> FRect:
    if isinstance(t, CustomRamp):
        if t.size.y > TILESIZE:
            x = t.pos.x * TILESIZE - offset.x
            y = (t.pos.y * TILESIZE) + TILESIZE - t.size.y - offset.y
            w = TILESIZE
            h = t.size.y
            return FRect(x, y, w, h)
        else:
            return FRect(t.pos.x * TILESIZE - offset.x, t.pos.y * TILESIZE - offset.y, TILESIZE, TILESIZE)
    elif isinstance(t, Ramp):
        x = t.pos.x * TILESIZE - offset.x
        y = (t.pos.y * TILESIZE) + TILESIZE - (TILESIZE * t.elevation) - offset.y
        w = TILESIZE
        h = TILESIZE * t.elevation
        return FRect(x, y, w, h)
    else:  # isinstance(t, Tile)
        return FRect(t.pos.x * TILESIZE - offset.x, t.pos.y * TILESIZE - offset.y, TILESIZE, TILESIZE)


def render_collision_mesh(surf: Surface, color: Color, t: Tile | Ramp, width: int = 1, offset: Vector2 = Vector2(0)) -> None:
    if isinstance(t, Ramp):
        r = tile_rect(t, offset=offset)
        p1, p2 = r.bottomleft, r.topright
        if t.type == TileType.RAMP_LEFT:
            p1, p2 = r.bottomright, r.topleft
        pygame.draw.rect(surf, color, r, width)
        pygame.draw.line(surf, color, p1, p2, width)
    elif isinstance(t, CustomRamp):
        r = tile_rect(t, offset=offset)
        p1, p2 = r.bottomleft, r.topright
        if t.orientation == TileType.RAMP_LEFT:
            p1, p2 = r.bottomright, r.topleft
        pygame.draw.rect(surf, color, r, width)
        pygame.draw.line(surf, color, p1, p2, width)
    else:  # isinstance(t, Tile) or isinstance(t, CustomTile)
        r = tile_rect(t, offset=offset)
        pygame.draw.rect(surf, color, r, width)


def serialize_chunk(chunk: Chunk, directory: str) -> None:
    chunk.__setattr__("_pre_renderd_surf", None)  # sonst Fehler, pickle kann pygame.Surface nicht bearbeiten
    chunk.__setattr__("parent", None)

    # for p, t in chunk._tiles.items():
    #     if t.type == TileType.TILE_CUSTOM:
    #         print(p, t.pos, p == tuple(t.pos))

    data = save_compressed_pickle(chunk)

    file_name = f"{directory}/{str(tuple(chunk.pos))}.data"
    with open(file_name, "wb+") as f:
        f.write(data)
