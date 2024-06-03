import os
from Scripts.CONFIG import *
from Scripts.utils import draw_text
from Scripts.tiles import TileMap, Tile, CustomTile

SAVING_SUB_FOLDER = 1

screen = pygame.display.set_mode(RES, 0, 32)
clock = pygame.time.Clock()
offset = Vector2(0)
mPos = Vector2(0)
highlight_tile_pos = Vector2(0)
x_off = 0
y_off = 0
clicks = [False, False, False]
tilemap = TileMap()
last_tile: Tile = None
tile_position = Vector2(0)
sub_tile_position = Vector2(0)
mode = 0
modes = [0, 1]
modes_desc = ["tile placing", "pixel placing"]
custom_tile = CustomTile(Vector2(10, 5))


def vector_equal(v1: Vector2, v2: Vector2) -> bool:
    return float(v1.x) == float(v2.x) and float(v1.y) == float(v2.y)


def render_grid():
    for y in range(-TILESIZE, int(RES.y) + TILESIZE, TILESIZE):
        for x in range(-TILESIZE, int(RES.x) + TILESIZE, TILESIZE):
            p = Vector2(x - x_off, y - y_off)
            rect = pygame.Rect(p.x, p.y, TILESIZE, TILESIZE)

            pygame.draw.rect(screen, "white", rect, 1)


def render_selected_tile():
    pygame.draw.rect(screen, "yellow", [tile_position.x * TILESIZE - offset.x, tile_position.y * TILESIZE - offset.y, TILESIZE, TILESIZE], 1)


def load() -> TileMap:
    return TileMap.deserialize("saves/t1")


def save(do_backup: bool = True):
    if do_backup:
        backup()
    tilemap.serialize(f"saves/t1")


def backup():
    idx = 0
    directory = f"saves/t{SAVING_SUB_FOLDER}"
    os.mkdir(f"{directory}/backup{idx}")
    for file_name in [f for f in os.listdir(f"{directory}/backup{idx}") if f.endswith(".data")]:
        os.remove(f"{directory}/backup{idx}/{file_name}")
    for file_name in [f for f in os.listdir(directory) if f.endswith(".data")]:
        os.replace(f"{directory}/{file_name}", f"{directory}/backup{idx}/{file_name}")


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
            if event.key == pygame.K_o:
                save()
            if event.key == pygame.K_i:
                tilemap = load()
            if event.key == pygame.K_u:
                backup()
            if event.key == pygame.K_g:
                mode = (mode + 1) % len(modes)

    keys = pygame.key.get_pressed()
    clicks = pygame.mouse.get_pressed()
    mPos = Vector2(pygame.mouse.get_pos())
    tile_position = Vector2(int((mPos[0] + offset.x) // TILESIZE), int((mPos[1] + offset.y) // TILESIZE))
    sub_tile_position = Vector2((mPos.x / TILESIZE) % 1 * 10, (mPos.y / TILESIZE) % 1 * 10)

    up = keys[pygame.K_w]
    left = keys[pygame.K_a]
    down = keys[pygame.K_s]
    right = keys[pygame.K_d]
    ctrl = keys[pygame.K_LCTRL]

    x_off = offset.x % TILESIZE
    y_off = offset.y % TILESIZE

    if up:
        offset.y -= 1 * (1 + int(ctrl) * 9)
    if down:
        offset.y += 1 * (1 + int(ctrl) * 9)
    if left:
        offset.x -= 1 * (1 + int(ctrl) * 9)
    if right:
        offset.x += 1 * (1 + int(ctrl) * 9)

    if clicks[0]:
        if mode == 0:
            last_tile = Tile(tile_position)
            tilemap.add(last_tile)
            tilemap.pre_render_chunks()
        elif mode == 1:
            custom_tile.add_pixel(sub_tile_position)
    if clicks[2]:
        if mode == 0:
            last_tile = None
            tilemap.remove(tile_position)
            tilemap.pre_render_chunks()
        elif mode == 1:
            custom_tile.remove_pixel(sub_tile_position)

    screen.fill((92, 95, 89))

    screen.blit(custom_tile.gen_surf(), custom_tile.pos * TILESIZE)

    render_grid()
    tilemap.render(screen, Vector2(0), offset=offset)
    render_selected_tile()

    draw_text(screen, f"Load with 'i' | Save wiht 'o'", (500, 10), color="yellow", background_color="black")
    draw_text(screen, f"TilePos: {highlight_tile_pos}", (10, 10), background_color="black")
    draw_text(screen, f"Offset: {offset}", (10, 40), background_color="black")
    draw_text(screen, f"Tile Offset: {Vector2(x_off, y_off)}", (10, 70), background_color="black")
    draw_text(screen, f"{last_tile}", (10, 110), background_color="black")
    draw_text(screen, f"{tile_position}", (10, 140), background_color="black")
    draw_text(screen, f"Mode: {modes_desc[mode]}", (10, 170), background_color="black")

    pygame.display.flip()

pygame.quit()
