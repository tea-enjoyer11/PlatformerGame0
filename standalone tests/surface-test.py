import pygame
import numpy as np
import time


pygame.display.set_mode((200, 200))


def is_surf_black(surf: pygame.Surface) -> bool:
    t1 = time.perf_counter()
    surf.lock()
    pixel_array = pygame.surfarray.array3d(surf)
    surf.unlock()
    print(time.perf_counter() - t1)
    return np.all(pixel_array == 0)


s1 = pygame.Surface((1000, 1000))
s1.set_colorkey((0, 0, 0))

s2 = pygame.image.load("test.png").convert()
s2.set_colorkey((0, 0, 0))


b1 = is_surf_black(s1)
b2 = is_surf_black(s2)

print(s1, s2, s1 == s2, s1 is s2, b1 == b2)
