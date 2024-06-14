import time
import pygame
from pygame import Rect, Surface, Vector2

pygame.init()

screen = pygame.display.set_mode((600, 600))
clock = pygame.time.Clock()


def create_mask(img):
    m = []
    for y in range(img.get_height()):
        arr = []
        for x in range(img.get_width()):
            col = img.get_at((x, y))
            if col == (0, 0, 0):
                arr.append(0)
            else:
                arr.append(1)
        m.append(arr)
    return m


img = pygame.transform.scale(pygame.image.load("greedy-meshing-img2.png").convert(), (600, 600))
mask = create_mask(img)


def greedy_meshing(mask):
    rects = []
    height = len(mask)
    width = len(mask[0])
    visited = [[False] * width for _ in range(height)]

    for y in range(height):
        for x in range(width):
            if mask[y][x] == 1 and not visited[y][x]:
                # Find the width of the rectangle
                rect_width = 0
                while x + rect_width < width and mask[y][x + rect_width] == 1 and not visited[y][x + rect_width]:
                    rect_width += 1

                # Find the height of the rectangle
                rect_height = 0
                done = False
                while y + rect_height < height and not done:
                    for k in range(rect_width):
                        if mask[y + rect_height][x + k] == 0 or visited[y + rect_height][x + k]:
                            done = True
                            break
                    if not done:
                        rect_height += 1

                # Mark the visited cells
                for dy in range(rect_height):
                    for dx in range(rect_width):
                        visited[y + dy][x + dx] = True

                # Add the rectangle to the list
                rects.append(Rect(x, y, rect_width, rect_height))

    return rects


t0 = time.perf_counter()
rects = greedy_meshing(mask)
print(time.perf_counter() - t0, "seconds to construct greedy mesh")

while True:
    screen.fill((0, 15, 98))
    mPos = Vector2(pygame.mouse.get_pos())
    dt = clock.tick(60) * 0.001
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            exit()

    mClicks = pygame.mouse.get_pressed()
    if mClicks[0]:
        print("test")
        img.set_at((mPos[0] // 6, mPos[1] // 6), (255, 255, 255))
        mask = create_mask(img)
        rectsd = greedy_meshing(mask)

    screen.blit(img, (0, 0))
    [pygame.draw.rect(screen, "yellow", r, width=1) for r in rects]

    pygame.display.flip()
