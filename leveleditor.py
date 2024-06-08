import os
import time
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
tile_position = Vector2(0)
sub_tile_position = Vector2(0)
mode = 0
modes = [0, 1]
modes_desc = ["tile placing", "pixel placing"]
brush_size = 0
brush_size_idx = 0
brush_sizes = [0, 1, 2, 3, 4, 5]
brush_type = 0
brush_types = [0, 1]  # 0=circle, 1=square
brush_type_idx = 0
brush_type_desc = ["circle", "square"]


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


def get_positions() -> list[Vector2]:
    positions = []
    center = tile_position

    if brush_type == 0:  # circle:
        for y in range(-brush_size, brush_size + 1):
            for x in range(-brush_size, brush_size + 1):
                pos = Vector2(center.x + x, center.y + y)
                distance = (pos - center).length()
                if distance <= brush_size:
                    positions.append(pos)
    elif brush_type == 1:  # square
        for y in range(-brush_size, brush_size + 1):
            for x in range(-brush_size, brush_size + 1):
                pos = Vector2(center.x + x, center.y + y)
                positions.append(pos)

    return positions


def get_pixel_positions() -> list[Vector2]:
    positions = []  # das sind offset pixel positions
    center = sub_tile_position

    if brush_type == 0:  # circle:
        for y in range(-brush_size, brush_size + 1):
            for x in range(-brush_size, brush_size + 1):
                pos = Vector2(center.x + x, center.y + y)
                distance = (pos - center).length()
                if distance <= brush_size:
                    positions.append(Vector2(x, y))
    elif brush_type == 1:  # square
        for y in range(-brush_size, brush_size + 1):
            for x in range(-brush_size, brush_size + 1):
                pos = Vector2(center.x + x, center.y + y)
                positions.append(Vector2(x, y))

    return positions


def load() -> TileMap:
    return TileMap.deserialize("saves/t1")


def save(do_backup: bool = False):
    if do_backup:
        backup()
    for file in os.scandir(f"saves/t1"):
        if file.name.endswith(".data"):
            os.unlink(file.path)
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
    dt = clock.tick(0)
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
            if event.key == pygame.K_h:
                brush_size_idx = (brush_size_idx + 1) % len(brush_sizes)
                brush_size = brush_sizes[brush_size_idx]
            if event.key == pygame.K_j:
                brush_type_idx = (brush_type_idx + 1) % len(brush_types)
                brush_type = brush_types[brush_type_idx]

    keys = pygame.key.get_pressed()
    clicks = pygame.mouse.get_pressed()
    last_mPos = mPos.copy()
    mPos = Vector2(pygame.mouse.get_pos())
    tile_position = Vector2(int((mPos[0] + offset.x) // TILESIZE), int((mPos[1] + offset.y) // TILESIZE))
    sub_tile_position = mPos + offset - tile_position * TILESIZE

    up = keys[pygame.K_w]
    left = keys[pygame.K_a]
    down = keys[pygame.K_s]
    right = keys[pygame.K_d]
    ctrl = keys[pygame.K_LCTRL]

    x_off = offset.x % TILESIZE
    y_off = offset.y % TILESIZE

    if up:
        offset.y -= 2 * (1 + int(ctrl) * 4) * 1 / 4 * dt
    if down:
        offset.y += 2 * (1 + int(ctrl) * 4) * 1 / 4 * dt
    if left:
        offset.x -= 2 * (1 + int(ctrl) * 4) * 1 / 4 * dt
    if right:
        offset.x += 2 * (1 + int(ctrl) * 4) * 1 / 4 * dt

    if clicks[0]:
        if mode == 0:
            for position in get_positions():
                tilemap.add(Tile(position))
            tilemap.pre_render_chunks()
        elif mode == 1:
            tt = 0
            # Old approach # 0.4 sekunden
            # for position in get_pixel_positions():
            #     t1 = time.perf_counter()
            #     tilemap.add_pixel(tile_position, position)
            #     tt += time.perf_counter() - t1

            # New approach # 0.003 sekunden
            positions = get_pixel_positions()
            t1 = time.perf_counter()
            tilemap.extend_pixels(positions, tile_position, sub_tile_position, color=(255, 255, 255))
            tt += time.perf_counter() - t1

            tilemap.pre_render_chunks()
            print(tt)
    if clicks[2]:
        if mode == 0:
            for position in get_positions():
                tilemap.remove(position)
            tilemap.pre_render_chunks()
        elif mode == 1:
            tt = 0
            positions = get_pixel_positions()
            t1 = time.perf_counter()
            tilemap.extend_pixels(positions, tile_position, sub_tile_position, color=(0, 0, 0))
            tt += time.perf_counter() - t1

            tilemap.pre_render_chunks()
            print(tt)

    screen.fill((92, 95, 89))

    render_grid()
    tilemap.render(screen, mPos + offset, offset=offset)
    render_selected_tile()

    draw_text(screen, f"Load with 'I' | Save wiht 'O'", (500, 10), color="yellow", background_color="black")
    draw_text(screen, f"Cycle placing modes with 'G'", (500, 40), color="yellow", background_color="black")
    draw_text(screen, f"Cycle brush sizes with 'H'", (500, 70), color="yellow", background_color="black")
    draw_text(screen, f"Cycle brush types with 'J'", (500, 100), color="yellow", background_color="black")
    draw_text(screen, f"Num Tiles: {tilemap.amount_of_tiles} | Num Chunks: {tilemap.amount_of_chunks}", (10, 10), background_color="black")
    draw_text(screen, f"Offset: {offset}", (10, 40), background_color="black")
    draw_text(screen, f"Tile Offset: {Vector2(x_off, y_off)}", (10, 70), background_color="black")
    draw_text(screen, f"TILEPOS: {tile_position} SUBTILEPOS: {sub_tile_position}", (10, 110), background_color="black")
    draw_text(screen, f"Mode: {modes_desc[mode]}", (10, 140), background_color="black")
    draw_text(screen, f"Brush strength: {brush_sizes[brush_size_idx]}", (10, 270), background_color="black")
    draw_text(screen, f"Brush type: {brush_type_desc[brush_type_idx]}", (10, 200), background_color="black")

    pygame.display.flip()
    pygame.display.set_caption(f"{clock.get_fps():.0f}")

pygame.quit()
