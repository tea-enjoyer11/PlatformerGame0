from cachetools import cached, LRUCache
from cachetools.keys import hashkey
import functools
import json

import pygame
import random

from Scripts.utils_math import clamp_number_to_range_steps, dist

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
        self.tilemap = {}
        self.offgrid_tiles = []
        self.grass_blades = {}

    def extract(self, id_pairs, keep=False):
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)

        for loc in self.tilemap:
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                matches[-1]['pos'] = matches[-1]['pos'].copy()
                matches[-1]['pos'][0] *= self.tile_size
                matches[-1]['pos'][1] *= self.tile_size
                if not keep:
                    del self.tilemap[loc]

        return matches

    def init_grass(self):
        grass = []
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            if tile["type"] == "grass_blades_cover":
                grass.append(tile)

        # anstatt manuell zu definieren → offsets = {0: 4, 1: 11, 2: 5, 3: 4, 4: 8, 5: 7, 6: 6}
        offsets = {i: 19 - img.get_height() // 2 for i, img in enumerate(self.game.assets["grass_blades"])}
        widths = {i: img.get_width() for i, img in enumerate(self.game.assets["grass_blades"])}
        print(offsets)
        for grass_tile in grass:
            pos = tuple(grass_tile["pos"])
            del self.tilemap[f"{pos[0]};{pos[1]}"]

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

    def update_grass(self, entity_rect: pygame.FRect, force_radius, force_dropoff):
        # TODO
        # einzelne blades müssen zusammen gepackt werden, damit lookup times nicht durch die Decke gehen.
        # Am besten alle blades in einem Tile gruppieren.
        # Dann vllt auch die mögliche state vom tile cachen??
        patches = []
        pos = entity_rect.center
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if check_loc in self.grass_blades:
                patches.append(self.grass_blades[check_loc])

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
                if blade["angle"] < force * 90:
                    blade["angle"] = min(max(dir * force * 90 + org_rot * 0.5, -90), 90)
                    clamp_number_to_range_steps(blade["angle"], -90, 90, 180/MAX_GRASS_STEPS)

    def get_around(self, pos, ignore: set[str] = set()):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap:
                t = self.tilemap[check_loc]
                if t["type"] not in ignore:
                    tiles.append(t)
        return tiles

    def get_tile(self, pos, convert_to_tilespace=False):
        if convert_to_tilespace:
            tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        else:
            tile_loc = pos
        check_loc = str(tile_loc[0]) + ';' + str(tile_loc[1])
        if check_loc in self.tilemap:
            return self.tilemap[check_loc]

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
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]['type'] in PHYSICS_TILES:
                return self.tilemap[tile_loc]

    def physics_rects_around(self, pos):
        rects = []
        # r = []
        for tile in self.get_around(pos):
            if tile["type"] in PHYSICS_TILES:
                rects.append(pygame.FRect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))
                # r.append(tile)
        # print(r)
        return rects

    def make_rect_from_tile(self, tile) -> pygame.FRect:
        return pygame.FRect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size)

    def autotile(self):
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                if check_loc in self.tilemap:
                    if self.tilemap[check_loc]['type'] == tile['type']:
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

    def render(self, surf, offset=(0, 0)):
        for tile in self.offgrid_tiles:
            surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1]))

        for x in range(int(offset[0] // self.tile_size), int((offset[0] + surf.get_width()) // self.tile_size + 1)):
            for y in range(int(offset[1] // self.tile_size), int((offset[1] + surf.get_height()) // self.tile_size + 1)):
                loc = str(x) + ';' + str(y)
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))

        for _, grass_patch in self.grass_blades.items():
            for tile in grass_patch["blades"]:
                # img, rect = make_rot(self.game, tile["variant"], tile["angle"], tuple(tile["pos"]))
                # t_pos = (int(_.split(";")[0]), int(_.split(";")[1]))
                a = make_rot(self.game, tile["variant"], tile["angle"], tuple(tile["pos"]))
                img, rect = a
                surf.blit(img, (rect.x - offset[0], rect.y - offset[1]))


MAX_GRASS_STEPS = 25


@functools.lru_cache(maxsize=None)
# @cached(cache={}, key=lambda game, variant, angle, b_pos, t_pos: hashkey(variant, angle, t_pos))
def make_rot(game, variant, angle, b_pos) -> tuple[pygame.Surface, pygame.FRect]:
    org_image: pygame.Surface = game.assets["grass_blades"][variant]
    org_rect = org_image.get_frect()
    org_rect.topleft = b_pos
    rot_image = pygame.transform.rotate(org_image, angle)
    rot_rect = rot_image.get_frect(center=org_rect.center)

    # print(org_rect, rot_rect)
    return (rot_image, rot_rect)
