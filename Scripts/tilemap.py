import functools
import json

import pygame
import random

from Scripts.utils_math import clamp_number_to_range_steps, dist
from Scripts.timer import Timer

AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8,
}

NEIGHBOR_OFFSETS = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]
PHYSICS_TILES = {'grass', 'stone', "bridge"}
AUTOTILE_TYPES = {'grass', 'stone'}
FALLTRHOGH_TILES = {"bridge"}


class TileMap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {"-3": {}, "-2": {}, "-1": {}, "0": {}, "1": {}, "2": {}, "3": {}}
        self.offgrid_tiles = []
        self.grass_blades = {}

    def extract(self, id_pairs, keep=False):
        layer = "0"
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)

        for loc in self.tilemap[layer]:
            tile = self.tilemap[layer][loc]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                matches[-1]['pos'] = matches[-1]['pos'].copy()
                matches[-1]['pos'][0] *= self.tile_size
                matches[-1]['pos'][1] *= self.tile_size
                if not keep:
                    del self.tilemap[layer][loc]

        return matches

    def init_grass(self):
        grass = []
        layer = "0"
        for loc in self.tilemap[layer]:
            tile = self.tilemap[layer][loc]
            if tile["type"] == "grass_blades_cover":
                grass.append(tile)

        # anstatt manuell zu definieren → offsets = {0: 4, 1: 11, 2: 5, 3: 4, 4: 8, 5: 7, 6: 6}
        offsets = {i: 19 - img.get_height() // 2 for i, img in enumerate(self.game.assets["grass_blades"])}
        widths = {i: img.get_width() for i, img in enumerate(self.game.assets["grass_blades"])}
        print(offsets)
        for grass_tile in grass:
            pos = tuple(grass_tile["pos"])
            del self.tilemap[layer][f"{pos[0]};{pos[1]}"]

            blades = []
            for n in range(int(self.tile_size/4)):
                variant = random.randint(0, len(self.game.assets["grass_blades"])-1)
                ox = n * int(self.tile_size/4)
                p = (
                    pos[0] * self.tile_size + ox,
                    pos[1] * self.tile_size + offsets[variant]
                )
                blades.append((p, variant))

            grass_patch = {"pos": grass_tile["pos"], "type": "grass_patch", "blades": []}
            for bpos in blades:
                grass_patch["blades"].append({"type": "grass_blades",
                                              "variant": bpos[1],
                                              "pos": list(bpos[0]),
                                              "angle": 0.0,
                                              "width": widths[bpos[1]]})

            self.grass_blades[f"{pos[0]};{pos[1]}"] = grass_patch

    def update_grass(self, entity_rects: list[pygame.FRect], force_radius, force_dropoff, particle_method=None):
        # TODO
        # einzelne blades müssen zusammen gepackt werden, damit lookup times nicht durch die Decke gehen.
        # Am besten alle blades in einem Tile gruppieren.
        # Dann vllt auch die mögliche state vom tile cachen??
        layer = "0"
        patches = []
        processed: set[tuple] = set()
        for pos in [rect.center for rect in entity_rects]:
            # pos = entity_rects[0].center
            tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
            if tile_loc in processed:
                continue
            processed.add(tile_loc)
            for offset in NEIGHBOR_OFFSETS:
                check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
                if check_loc in self.grass_blades:
                    patches.append(self.grass_blades[check_loc])

            hit_blades = []
            for patch in patches:
                for blade in patch["blades"]:
                    org_rot = blade["angle"]
                    dis = dist(blade["pos"], pos)
                    if dis < force_radius:
                        force = 2
                    else:
                        dis = max(0, dis - force_radius)
                        force = 1 - min(dis / force_dropoff, 1)
                    dir = -1 if pos[0] < blade["pos"][0] else 1
                    # dont update unless force is stronger
                    if abs(blade["angle"]) < force * 90:
                        blade["angle"] = min(max(dir * force * 90 + org_rot * 0.5, -90), 90)
                        blade["angle"] = clamp_number_to_range_steps(blade["angle"], -90, 90, 180/MAX_GRASS_STEPS)
                        if dis < 5:
                            hit_blades.append(blade)

            if particle_method and hit_blades:
                if random.random() * 100 > 99:
                    for blade in hit_blades:
                        particle_method("leaf", pygame.Rect(*blade["pos"], 4, 4), (random.random()*100-50, -100))

    def caculate_tile_span(self, size: int):
        if size <= self.tile_size:
            return 0
        return (size + self.tile_size - 1) // self.tile_size - 1

    def get_around(self, pos, size=(16, 16), ignore: set[str] = set()):
        layer = "0"
        tiles = []
        topleft_tile = (
            int(pos[0] // self.tile_size),
            int(pos[1] // self.tile_size)
        )
        bottomright_tile = (
            int(pos[0] // self.tile_size) + self.caculate_tile_span(size[0]),
            int(pos[1] // self.tile_size) + self.caculate_tile_span(size[1])
        )
        for x in range(topleft_tile[0], bottomright_tile[0]+1):
            for y in range(topleft_tile[1], bottomright_tile[1]+1):
                for offset in NEIGHBOR_OFFSETS:
                    check_loc = str(x + offset[0]) + ';' + str(y + offset[1])
                    if check_loc in self.tilemap[layer]:
                        t = self.tilemap[layer][check_loc]
                        if t["type"] not in ignore and t not in tiles:
                            tiles.append(t)
        return tiles

    def get_tile(self, pos, convert_to_tilespace=False):
        layer = "0"
        if convert_to_tilespace:
            tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        else:
            tile_loc = pos
        check_loc = str(tile_loc[0]) + ';' + str(tile_loc[1])
        if check_loc in self.tilemap[layer]:
            return self.tilemap[layer][check_loc]

    def save(self, path):
        f = open(path, 'w')
        json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size, 'offgrid': self.offgrid_tiles}, f)
        f.close()

    def load(self, path):
        f = open(path, 'r')
        map_data = json.load(f)
        f.close()

        self.tilemap = map_data['tilemap']
        self.tile_size = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']

    def solid_check(self, pos):
        layer = "0"
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tile_loc in self.tilemap[layer]:
            if self.tilemap[layer][tile_loc]['type'] in PHYSICS_TILES:
                return self.tilemap[layer][tile_loc]

    def physics_rects_around(self, pos, size=(16, 16)):
        rects = []
        # r = []
        for tile in self.get_around(pos, size=size):
            if tile["type"] in PHYSICS_TILES:
                rects.append(pygame.FRect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))
                # r.append(tile)
        # print(r)
        return rects

    def make_rect_from_tile(self, tile) -> pygame.FRect:
        return pygame.FRect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size)

    def autotile(self, layer="0"):
        for loc in self.tilemap[layer]:
            tile = self.tilemap[layer][loc]
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                if check_loc in self.tilemap[layer]:
                    if self.tilemap[layer][check_loc]['type'] == tile['type']:
                        neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            if (tile['type'] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbors]

    def rotate_grass(self, rot_function):
        for _, patch in self.grass_blades.items():
            for tile in patch["blades"]:
                tile["angle"] = rot_function(tile["pos"][0])
                tile["angle"] = clamp_number_to_range_steps(tile["angle"], -90, 90, 180/MAX_GRASS_STEPS)
                # print(tile["angle"], make_rot.cache_info())

    def render(self, surf: pygame.Surface, offset=(0, 0), render_only=None):
        for tile in self.offgrid_tiles:
            surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1]))

        # layer = "0"
        for layer_ in range(-3, 3+1):
            layer = str(layer_)
            if render_only:
                if layer != render_only:
                    continue
            # shading = 255 - abs(layer_) * 50
            # tsurf = pygame.Surface(surf.get_size())
            for x in range(int(offset[0] // self.tile_size), int((offset[0] + surf.get_width()) // self.tile_size + 1)):
                for y in range(int(offset[1] // self.tile_size), int((offset[1] + surf.get_height()) // self.tile_size + 1)):
                    loc = str(x) + ';' + str(y)
                    if loc in self.tilemap[layer]:
                        tile = self.tilemap[layer][loc]
                        surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))
            # tsurf.set_alpha(shading)
            # surf.blit(tsurf, (0, 0))
        for _, grass_patch in self.grass_blades.items():
            for tile in grass_patch["blades"]:
                img, rect = make_rot(self.game, tile["variant"], tile["angle"], tuple(tile["pos"]))
                surf.blit(img, (rect.x - offset[0], rect.y - offset[1]))


MAX_GRASS_STEPS = 25


def make_rot(game, variant, angle, b_pos) -> tuple[pygame.Surface, pygame.FRect]:
    org_image: pygame.Surface = game.assets["grass_blades"][variant]
    org_rect = org_image.get_frect()
    org_rect.topleft = b_pos
    rot_image = make_rot_image(game, variant, angle)
    rot_rect = rot_image.get_frect(center=org_rect.center)

    return (rot_image, rot_rect)


@ functools.lru_cache(maxsize=256)
def make_rot_image(game, variant, angle) -> pygame.Surface:
    org_image: pygame.Surface = game.assets["grass_blades"][variant]
    rot_image = pygame.transform.rotate(org_image, angle)
    return rot_image
