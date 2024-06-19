import pygame
from pygame import Surface, Rect, Vector2


def load_image(path: str, flip_x: bool = False, flip_y: bool = False) -> Surface:
    i = pygame.image.load(path).convert()
    i = pygame.transform.flip(i, flip_x=flip_x, flip_y=flip_y)
    i.set_colorkey("black")
    return i


class Blade:
    def __init__(self) -> None:
        pass


master_screen = pygame.display.set_mode((600, 600))
screen = Surface((100, 100))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            exit()

    screen.fill((89, 25, 124))
    master_screen.blit(pygame.transform.scale(screen, (600, 600)), (0, 0))
    pygame.display.flip()
