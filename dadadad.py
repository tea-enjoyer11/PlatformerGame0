from Scripts.utils import hex_to_rgb, palette_sawp, load_image
import pygame
from itertools import chain
import time


class Example:
    def __init__(self):
        # self._tiles = {'a': 1, 'b': 2}
        # self._ghost_tiles = {'c': 3, 'd': 4}
        self._tiles = {f'key_{i}': i for i in range(1000000)}
        self._ghost_tiles = {f'ghost_key_{i}': i for i in range(1000000, 2000000)}

    def combine_items1(self):
        # Option 1: Using update method
        combined_dict = {}
        combined_dict.update(self._tiles)
        combined_dict.update(self._ghost_tiles)
        combined_items_1 = combined_dict.items()
        return None
        return combined_items_1

    def combine_items2(self):
        # Option 2: Using dictionary comprehension
        combined_dict_2 = {**self._tiles, **self._ghost_tiles}
        combined_items_2 = combined_dict_2.items()
        return None
        return combined_dict_2

    def combine_items3(self):

        # Option 3: Using itertools.chain
        from itertools import chain
        combined_items_3 = chain(self._tiles.items(), self._ghost_tiles.items())

        # Return all combined items as lists for demonstration
        return None
        return combined_items_3


# example = Example()

# t1 = time.perf_counter()
# print("Combined items (update):", example.combine_items1())
# print(time.perf_counter() - t1)
# t1 = time.perf_counter()
# print("Combined items (comprehension):", example.combine_items2())
# print(time.perf_counter() - t1)
# t1 = time.perf_counter()
# print("Combined items (chain):", example.combine_items3())
# print(time.perf_counter() - t1)

# print(hash(example.combine_items3()))


screen = pygame.display.set_mode((600, 600))

s = pygame.Surface((100, 100))
oi = pygame.image.load("assets/tile.png").convert()
ni = palette_sawp(oi, [hex_to_rgb("#37446E"), hex_to_rgb("#232B5C"), hex_to_rgb("#8AABBC"), hex_to_rgb("#3A002F")], [(200, 200, 200), (180, 180, 180), (160, 160, 160), (140, 140, 140)])

while True:
    s.blit(oi, (0, 0))
    s.blit(ni, (64, 0))
    screen.blit(pygame.transform.scale(s, (600, 600)), (0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()

    pygame.display.flip()
x
