import pygame
from pygame import Mask, Surface
from pygame.mask import from_surface

pygame.init()

screen = pygame.display.set_mode((200, 200))
clock = pygame.time.Clock()

surf1 = pygame.image.load("0.png").convert()
surf2 = pygame.image.load("1.png").convert()
surf3 = pygame.image.load("2.png").convert()
surf1.set_colorkey((0, 0, 0))
surf2.set_colorkey((0, 0, 0))
surf3.set_colorkey((0, 0, 0))
m1 = from_surface(surf1)
m2 = from_surface(surf2)
m3 = from_surface(surf3)
m4 = from_surface(surf3)
m1surf = m1.to_surface()
m1surf.set_colorkey((0, 0, 0))
m2surf = m2.to_surface()
m2surf.set_colorkey((0, 0, 0))
m3surf = m3.to_surface()
m3surf.set_colorkey((0, 0, 0))

while True:
    screen.fill((0, 15, 98))
    mPos = pygame.mouse.get_pos()
    dt = clock.tick(60) * 0.001
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            exit()

    overlapPoint = m3.overlap(m1, mPos)
    m4 = from_surface(surf3)
    m4.erase(m1, mPos)

    # screen.blit(surf1, (0, 0))
    screen.blit(m1surf, mPos)
    screen.blit(m3surf, (0, 0))
    screen.blit(m4.to_surface(), (100, 100))

    if overlapPoint:
        pygame.draw.circle(screen, "red", overlapPoint, 1)

    pygame.display.flip()
