from Scripts.CONFIG import *
from Scripts.utils import draw_text

screen = pygame.display.set_mode(RES, 0, 32)
clock = pygame.time.Clock()
offset = Vector2(0)
mPos = Vector2(0)
highlight_tile_pos = Vector2(0)
x_off = 0
y_off = 0


def vector_equal(v1: Vector2, v2: Vector2) -> bool:
    return float(v1.x) == float(v2.x) and float(v1.y) == float(v2.y)


def render_grid():
    for y in range(-TILESIZE, int(RES.y) + TILESIZE, TILESIZE):
        for x in range(-TILESIZE, int(RES.x) + TILESIZE, TILESIZE):
            c = "white"
            p = Vector2(x - x_off, y - y_off)
            rect = pygame.Rect(p.x, p.y, TILESIZE, TILESIZE)

            if vector_equal(p // TILESIZE, highlight_tile_pos):
                c = "red"
            pygame.draw.rect(screen, c, rect, 1)


up = False
left = False
right = False
down = False
ctrl = False


run = True
while run:
    dt = clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            run = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                offset = Vector2(0)

    keys = pygame.key.get_pressed()
    mPos = Vector2(pygame.mouse.get_pos())
    up = keys[pygame.K_w]
    left = keys[pygame.K_a]
    down = keys[pygame.K_s]
    right = keys[pygame.K_d]
    ctrl = keys[pygame.K_LCTRL]

    x_off = offset.x % TILESIZE
    y_off = offset.y % TILESIZE
    highlight_tile_pos = mPos // TILESIZE - Vector2(x_off, y_off)

    if up:
        offset.y -= 1 * (1 + int(ctrl) * 3)
    if down:
        offset.y += 1 * (1 + int(ctrl) * 3)
    if left:
        offset.x -= 1 * (1 + int(ctrl) * 3)
    if right:
        offset.x += 1 * (1 + int(ctrl) * 3)

    screen.fill((92, 95, 89))

    render_grid()

    draw_text(screen, f"TilePos: {highlight_tile_pos}", (10, 10), background_color="black")
    draw_text(screen, f"Offset: {offset}", (10, 40), background_color="black")
    draw_text(screen, f"Tile Offset: {Vector2(x_off, y_off)}", (10, 70), background_color="black")

    pygame.display.flip()

pygame.quit()
