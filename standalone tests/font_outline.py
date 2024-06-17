# from https://stackoverflow.com/questions/54363047/how-to-draw-outline-on-the-fontpygame

import pygame

_circle_cache = {}


def _circlepoints(r):
    r = int(round(r))
    if r in _circle_cache:
        return _circle_cache[r]
    x, y, e = r, 0, 1 - r
    _circle_cache[r] = points = []
    while x >= y:
        points.append((x, y))
        y += 1
        if e < 0:
            e += 2 * y - 1
        else:
            x -= 1
            e += 2 * (y - x) - 1
    points += [(y, x) for x, y in points if x > y]
    points += [(-x, y) for x, y in points if x]
    points += [(x, -y) for x, y in points if y]
    points.sort()
    return points


def render(text, font, gfcolor=pygame.Color('dodgerblue'), ocolor=(255, 255, 255), opx=2):
    textsurface = font.render(text, True, gfcolor).convert_alpha()
    w = textsurface.get_width() + 2 * opx
    h = font.get_height()

    osurf = pygame.Surface((w, h + 2 * opx)).convert_alpha()
    osurf.fill((0, 0, 0, 0))

    surf = osurf.copy()

    osurf.blit(font.render(text, True, ocolor).convert_alpha(), (0, 0))

    for dx, dy in _circlepoints(opx):
        surf.blit(osurf, (dx + opx, dy + opx))

    surf.blit(textsurface, (opx, opx))
    return surf


def main():
    pygame.init()

    font = pygame.font.SysFont("Arial", 64)

    screen = pygame.display.set_mode((600, 600))
    clock = pygame.time.Clock()

    while True:
        dt = clock.tick(0) * 0.001
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
        screen.fill((30, 30, 30))

        screen.blit(render(f'{clock.get_fps():.4f}', font), (20, 20))

        pygame.display.update()


if __name__ == '__main__':
    main()
