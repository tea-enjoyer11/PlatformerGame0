from copy import deepcopy
import os
from Scripts.CONFIG import *
from Scripts.CONFIG import Vector2
from typing import Literal


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
    RAMP_LEFT = auto()
    RAMP_RIGHT = auto()
    RAMP_CUSTOM = auto()


class Tile:
    __slots__ = ("pos", "type", "img_idx", "size")

    def __init__(self, pos: Vector2, tile_type: TileType = TileType.TILE) -> None:
        if not isinstance(pos, Vector2):
            pos = Vector2(pos)
        self.pos = pos
        self.type = tile_type

        self.size = (TILESIZE, TILESIZE)
        self.img_idx = 0

    def __repr__(self) -> str:
        return f"<{self.pos=}, {self.type=}, {self.img_idx=}>"

    def serialize(self):
        attrs = []
        s = ""

        # cls = self.__class__
        # while cls != object:
        #     if '__slots__' in cls.__dict__:
        #         for val in cls.__slots__:
        #             print(f"{cls.__name__}.{val} = {getattr(self, val)}")
        #             attrs.append(val)
        #     cls = cls.__bases__[0]

        # for attr in attrs:
        #     s += str(SerializeTypes.__getitem__(attr).value)

        for _type in SerializeTypes:
            try:
                if a := self.__getattribute__(_type.name):
                    s += "!" + str(a)
            except AttributeError:
                pass
        s = s[1:]
        s = s.replace(" ", "")
        ss = save_pickle(s)
        sss = save_compressed_pickle(s)
        ssss = save_compressed_pickle(self)
        sssss = save_pickle(self)
        print(len(s), len(ss), len(sss), len(ssss), len(sssss))


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
    def parse_data(hitbox: Surface) -> ...:
        ret: dict[int, int] = {}
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


class Chunk:
    __slots__ = ("parent", "pos", "size", "_tiles", "_ghost_tiles", "_pre_renderd_surf",
                 "_pre_renderd_surf_size", "pre_render_offset")
    default_pre_renderd_surf_size = Vector2(CHUNKSIZE * TILESIZE, CHUNKSIZE * TILESIZE)

    def __init__(self, parent: "TileMap", pos: Vector2, size) -> None:
        self.parent = parent
        self.pos = Vector2(pos)
        self.size = size
        self._tiles: dict[tuple, Tile] = {}
        self._ghost_tiles: dict[tuple, Tile] = {}

        self._pre_renderd_surf: Surface = None
        self._pre_renderd_surf_size: Vector2 = None
        self.pre_render_offset = Vector2(0)

    def copy(self) -> "Chunk":
        return deepcopy(self)

    def get(self, pos: tuple) -> Tile | None:
        if pos in self._tiles:
            return self._tiles[pos]
        return None

    def get_all(self) -> list[Tile]:
        return list(self._tiles.values())

    def get_around(self, pos: Vector2, size: Vector2 | None = None) -> list[Tile | Ramp]:
        ret: list[Tile | Ramp] = []

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
        x_off = -int(en_size.x // 2)
        y_off = -int(en_size.y // 2)
        for x__ in range(int(en_size[0])):
            for y__ in range(int(en_size[1])):
                for x_, y_ in NEIGHBOR_OFFSETS:
                    p = (x_off + x + x_ + x__, y_off + y + y_ + y__)
                    if p in self._tiles:
                        ret.append(self._tiles[p])
                    if p in self._ghost_tiles:
                        ret.append(self._ghost_tiles[p])
        return ret

    def is_empty(self) -> bool:
        return len(self._tiles)

    def remove(self, pos: Vector2) -> None:
        pos = (pos[0] % CHUNKSIZE, pos[1] % CHUNKSIZE)
        if pos in self._tiles:
            del self._tiles[pos]

    def add(self, tile: Tile) -> None:
        pos = tuple(tile.pos)
        pos = (pos[0] % CHUNKSIZE, pos[1] % CHUNKSIZE)
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

    def extend(self, tiles: list[Tile]) -> None:
        for tile in tiles:
            pos = tuple(tile.pos)
            pos = (pos[0] % CHUNKSIZE, pos[1] % CHUNKSIZE)
            self._tiles[pos] = tile

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
            list[bool]: [on_top_edge, on_right_edge, on_bottom_edge, on_left_edge]
        """
        x, y = tile.pos.x % CHUNKSIZE, tile.pos.y % CHUNKSIZE
        additional_w, additional_h = tuple(Vector2(tile_rect(tile).size) // TILESIZE - Vector2(1))
        x = min(self.size[0], x + additional_w)
        y = max(0, y - additional_h)

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
        l = []
        global_tile_offset = Vector2(0)

        # ! Smart approach
        ramps, custom_ramps, tiles = [], [], []
        for _, tile in self._tiles.items():
            if tile.type in [TileType.RAMP_LEFT, TileType.RAMP_RIGHT]:
                ramps.append(tile)
            elif tile.type == TileType.RAMP_CUSTOM:
                custom_ramps.append(tile)
            else:
                tiles.append(tile)

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

        for c_ramp in custom_ramps:
            local_pos = (c_ramp.pos.x % CHUNKSIZE, c_ramp.pos.y % CHUNKSIZE)
            offset_y = c_ramp.size.y - TILESIZE
            local_pos = (local_pos[0] * TILESIZE, local_pos[1] * TILESIZE + global_tile_offset.y - offset_y)
            l.append((IMGS[c_ramp.img_idx], local_pos))
            # print(local_pos)

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

    def remove(self, pos: Vector2) -> None:
        related_chunk_pos = (pos.x // self.chunk_size[0], pos.y // self.chunk_size[1])
        if related_chunk_pos in self._chunks:
            self._chunks[related_chunk_pos].remove(pos)
            if not self._chunks[related_chunk_pos].is_empty():
                del self._chunks[related_chunk_pos]

    def add(self, tile: Tile) -> None:
        related_chunk_pos = (tile.pos.x // self.chunk_size[0], tile.pos.y // self.chunk_size[1])
        # print(related_chunk_pos)

        if related_chunk_pos not in self._chunks:
            # chunk_pos = (related_chunk_pos[0] * TILESIZE, related_chunk_pos[1] * TILESIZE)
            self._chunks[related_chunk_pos] = Chunk(self, related_chunk_pos, size=self.chunk_size)

        chunk = self._chunks[related_chunk_pos]
        chunk.add(tile)
        self.amount_of_tiles += 1

    def extend(self, tiles: list[Tile]) -> None:
        for tile in tiles:
            # self._tiles[tuple(tile.pos)] = tile

            related_chunk_pos = (tile.pos.x // self.chunk_size[0], tile.pos.y // self.chunk_size[1])
            # print(related_chunk_pos)

            if related_chunk_pos not in self._chunks:
                # chunk_pos = (related_chunk_pos[0] * TILESIZE, related_chunk_pos[1] * TILESIZE)
                self._chunks[related_chunk_pos] = Chunk(self, related_chunk_pos, size=self.chunk_size)

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

    def get_chunk(self, pos: tuple) -> Chunk | None:
        if pos in self._chunks:
            return self._chunks[pos]
        return None

    def _create_empty_chunk(self, pos: tuple) -> Chunk | None:
        if pos not in self._chunks:
            c = Chunk(self, pos, self.chunk_size)
            self._chunks[pos] = c
            return c
        return None

    def get_around(self, pos: Vector2) -> list[Tile]:
        related_chunk_pos = Vector2(pos.x // TILESIZE // self.chunk_size[0], pos.y // TILESIZE // self.chunk_size[1])
        # print("related chunk position:", related_chunk_pos, pos)
        ret = []

        # ! New approach
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

        # ! Old approach
        # for offset in NEIGHBOR_OFFSETS:
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

    def serialize(self, directory: str) -> None:
        for chunk in self._chunks.values():
            serialize_chunk(chunk.copy(), directory)

    @staticmethod
    def deserialize(directory: str) -> "TileMap":
        # load ...
        chunks: dict[tuple, Chunk] = {}
        tilemap = TileMap()

        files = [f for f in os.listdir(directory) if f.endswith(".data")]
        for file_path in files:
            c: Chunk = None
            with open(directory + "/" + file_path, "rb") as f:
                data = f.read()
                c = load_compressed_pickle(data)
            if c:
                c.parent = tilemap
                chunks[tuple(c.pos)] = c
        tilemap._chunks = chunks
        tilemap.pre_render_chunks()
        return tilemap


def collision_test(object_1: Rect, object_list: list[Rect]) -> list[Rect]:
    collision_list = []
    for obj in object_list:
        if obj.colliderect(object_1):
            collision_list.append(obj)
    return collision_list


def tile_rect(t: Tile | Ramp, offset: Vector2 = Vector2(0)) -> Rect:
    if isinstance(t, CustomRamp):
        if t.size.y > TILESIZE:
            x = t.pos.x * TILESIZE - offset.x
            y = (t.pos.y * TILESIZE) + TILESIZE - t.size.y - offset.y
            w = TILESIZE
            h = t.size.y
            return Rect(x, y, w, h)
        else:
            return Rect(t.pos.x * TILESIZE - offset.x, t.pos.y * TILESIZE - offset.y, TILESIZE, TILESIZE)
    elif isinstance(t, Ramp):
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
    elif isinstance(t, CustomRamp):
        r = tile_rect(t, offset=offset)
        p1, p2 = r.bottomleft, r.topright
        if t.orientation == TileType.RAMP_LEFT:
            p1, p2 = r.bottomright, r.topleft
        pygame.draw.rect(surf, color, r, width)
        pygame.draw.line(surf, color, p1, p2, width)
    else:  # isinstance(t, Tile)
        r = tile_rect(t, offset=offset)
        pygame.draw.rect(surf, color, r, width)


def serialize_chunk(chunk: Chunk, directory: str) -> None:
    chunk.__setattr__("_pre_renderd_surf", None)  # sonst Fehler, pickle kann pygame.Surface nicht bearbeiten
    chunk.__setattr__("parent", None)
    data = save_compressed_pickle(chunk)

    file_name = f"{directory}/{str(tuple(chunk.pos))}.data"
    with open(file_name, "wb+") as f:
        f.write(data)


def deserialize_chunk(chunk: Chunk, file_path: str) -> Chunk | None:
    data: bytes = None

    with open(file_path, "rb") as f:
        data = f.read()

    if data:
        chunk = load_compressed_pickle(data)
        return chunk
    return None
