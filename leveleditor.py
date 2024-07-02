import os
import time
from Scripts.CONFIG import *
from Scripts.utils import draw_text
from Scripts.utils_math import clamp
from Scripts.tiles import TileMap, Tile, CustomTile, GrassBlade
from Scripts.timer import Timer, TimerManager
SAVING_SUB_FOLDER = 1


def parse_master_tile_set(path: str, bg_color=(36, 0, 36)) -> list[list[Surface]]:
    master_tile_set = load_image(path)
    real_size = Vector2(master_tile_set.get_size())
    size = Vector2(real_size.x / TILESIZE, real_size.y / TILESIZE)
    offset_ = Vector2(2, 2)
    ret: list[list[Surface]] = []
    for y in range(int(size.y) - 2):
        row = []
        for x in range(int(size.x) - 1):
            r = Rect(x * TILESIZE + offset_.x * x, y * TILESIZE + offset_.y * y, TILESIZE, TILESIZE)
            try:
                row.append(master_tile_set.subsurface(r))
            except ValueError:
                print("ERROR: subsurface outside of surface! Rect:", r)
        ret.append(row)
    return ret


timermanager = TimerManager()
RES = Vector2(1200, 700)
left_menu_offset = 500
tile_displaying_offset = 4
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
tool = 0
tools = [0, 1]
tools_desc = ["brush", "rect"]
rect_tool_start: Vector2 = None
rect_tool_end: Vector2 = None
do_rect_tool = False
selected_tile = (0, 0)
hold_to_place = True
last_mClicks = (False, False, False)
click_timer = Timer(0.1, True, True)
# tile set
tiles = parse_master_tile_set("assets/tileset template.png")

for f in os.listdir("assets/tiles/grass_blades"):
    GrassBlade.img_cache[f"{f.split('.')[0]};{0}"] = load_image(f"assets/tiles/grass_blades/{f}")
    GrassBlade.offset_cache[f"{f.split('.')[0]};{0}"] = Vector2(0, 0)
    GrassBlade.img_half_size_cache[f"{f.split('.')[0]};{0}"] = tuple(Vector2(load_image(f"assets/tiles/grass_blades/{f}").get_size()) // 2)


def render_grid():
    for y in range(-TILESIZE, int(RES.y) + TILESIZE, TILESIZE):
        for x in range(left_menu_offset - TILESIZE, int(RES.x) + TILESIZE, TILESIZE):
            p = Vector2(x - x_off, y - y_off)
            rect = pygame.Rect(p.x - 4, p.y, TILESIZE, TILESIZE)

            pygame.draw.rect(screen, "white", rect, 1)


def render_selected_tile():
    if mPos.x > left_menu_offset:
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


def get_mouse_pressed() -> tuple[bool, bool, bool]:
    if hold_to_place:
        return pygame.mouse.get_pressed()

    a = pygame.mouse.get_pressed()
    ret = [False, False, False]
    for i, v in enumerate(a):
        if not last_mClicks[i]:
            ret[i] = a[i]

    return tuple(ret)


up = False
left = False
right = False
down = False
ctrl = False


run = True
while run:
    last_mClicks = pygame.mouse.get_pressed()
    timermanager.update()
    dt = clock.tick(0)
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            run = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                offset = Vector2(0)
            if event.key == pygame.K_t:
                tool = (tool + 1) % len(tools)
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
            if event.key == pygame.K_q:
                hold_to_place = not hold_to_place

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if tool == 1:  # rect tool
                rect_tool_start = mPos + offset
        elif event.type == pygame.MOUSEBUTTONUP:
            if tool == 1:  # rect tool
                rect_tool_end = mPos
                do_rect_tool = True

    if rect_tool_start and not do_rect_tool:
        rect_tool_end = mPos

    keys = pygame.key.get_pressed()
    clicks = get_mouse_pressed()
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

    if clicks[0] and click_timer:
        if mPos.x < left_menu_offset:  # menu
            p = mPos // (TILESIZE + tile_displaying_offset)
            if p.y < len(tiles) and p.x < len(tiles[0]):
                selected_tile = (
                    clamp(0, int(p.y), len(tiles) - 1),
                    clamp(0, int(p.x), len(tiles[0]) - 1)
                )
        else:  # tile placing
            if tool == 0:
                if mode == 0:
                    offgrid = False
                    for position in get_positions():
                        idx = f"c_tile({selected_tile[1]};{selected_tile[0]})"
                        if selected_tile in [(14, 0), (14, 1), (14, 2), (15, 0), (15, 1), (15, 2), (16, 0), (16, 1), (16, 2)]:
                            t = Tile(position, img_idx=f"TEST{idx}")
                        elif selected_tile in [(14, 3), (14, 4), (14, 5), (14, 6), (14, 7), (14, 8), (14, 9)]:
                            img_idx = f"{selected_tile[1]-3}"
                            p = mPos - Vector2(GrassBlade.img_cache[f"{img_idx};0"].get_size()) / 2
                            t = GrassBlade((p + offset) / TILESIZE, img_idx=img_idx)
                            t.img_idx = f"{img_idx};0"
                            offgrid = True
                            print(selected_tile, img_idx, t.img_idx)
                        else:
                            t = CustomTile(position, idx, idx)
                        if offgrid:
                            tilemap.add_offgrid(t)
                        else:
                            tilemap.add(t)
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
        if mPos.x < left_menu_offset:
            ...
        else:
            if tool == 0:
                if mode == 0:
                    offgrid = False
                    for position in get_positions():
                        if selected_tile in [(14, 3), (14, 4), (14, 5), (14, 6), (14, 7), (14, 8), (14, 9)]:
                            offgrid = True
                        if offgrid:
                            img_idx = f"{selected_tile[1]-3}"
                            p = mPos - Vector2(GrassBlade.img_cache[f"{img_idx};0"].get_size()) / 2
                            tilemap.remove_offgrid((p + offset) / TILESIZE)
                        else:
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

    if do_rect_tool:
        print(rect_tool_start, rect_tool_end)

        tile_pos_start = rect_tool_start // TILESIZE
        tile_pos_end = (rect_tool_end + offset) // TILESIZE

        # ...

        print(tile_pos_start, tile_pos_end)

        rect_tool_start = None
        rect_tool_end = None
        do_rect_tool = False

    #
    # Render Part
    #
    screen.fill((92, 95, 89))
    render_grid()
    tilemap.render(screen, mPos + offset, offset=offset)  # TODO so was wie: culling_rect=Rect(left_menu_offset, 0, RES.x - left_menu_offset, RES.y) einbauen
    render_selected_tile()

    # display tiles & current tile
    pygame.draw.rect(screen, (70, 0, 70), Rect(0, 0, left_menu_offset, RES.y))  # left ui panel background
    for y, row in enumerate(tiles):
        for x, surf in enumerate(row):
            p = Vector2(x * TILESIZE, y * TILESIZE)
            p += Vector2(tile_displaying_offset * x, tile_displaying_offset * y)
            screen.blit(surf, p)
    pygame.draw.rect(screen, "red", Rect(selected_tile[1] * (TILESIZE + tile_displaying_offset) - tile_displaying_offset / 2, selected_tile[0] * (TILESIZE + tile_displaying_offset) - tile_displaying_offset / 2, TILESIZE + tile_displaying_offset, TILESIZE + tile_displaying_offset), int(tile_displaying_offset / 2))

    # rect tool
    if rect_tool_start:
        # inversing rect sodass auch links und nach oben gezogen werden kann
        x = rect_tool_start.x - offset.x
        y = rect_tool_start.y - offset.y
        w = rect_tool_end.x - rect_tool_start.x + offset.x
        h = rect_tool_end.y - rect_tool_start.y + offset.y
        r = Rect(x, y, w, h)
        print(r)
        pygame.draw.rect(screen, "yellow", r, 2)

    # ui
    left_ui_pos = left_menu_offset + 10
    right_ui_pos = RES.x - 300
    screen.blit(pygame.transform.scale(tiles[selected_tile[0]][selected_tile[1]], (80, 80)), (left_ui_pos - 100, 20))
    draw_text(screen, f"Load with 'I' | Save wiht 'O'", (right_ui_pos, 10), color="yellow", background_color="black")
    draw_text(screen, f"Cycle placing modes with 'G'", (right_ui_pos, 40), color="yellow", background_color="black")
    draw_text(screen, f"Cycle brush sizes with 'H'", (right_ui_pos, 70), color="yellow", background_color="black")
    draw_text(screen, f"Cycle brush types with 'J'", (right_ui_pos, 100), color="yellow", background_color="black")
    draw_text(screen, f"Cycle tools with 'T'", (right_ui_pos, 130), color="yellow", background_color="black")
    draw_text(screen, f"Num Tiles: {tilemap.amount_of_tiles} | Num Chunks: {tilemap.amount_of_chunks}", (left_ui_pos, 10), background_color="black")
    draw_text(screen, f"Offset: {offset}", (left_ui_pos, 40), background_color="black")
    draw_text(screen, f"Tile Offset: {Vector2(x_off, y_off)}", (left_ui_pos, 70), background_color="black")
    draw_text(screen, f"TILEPOS: {tile_position} SUBTILEPOS: {sub_tile_position} CHUNKPOS: {mPos//CHUNKSIZE}", (left_ui_pos, 110), background_color="black")
    draw_text(screen, f"Mode: {modes_desc[mode]}", (left_ui_pos, 140), background_color="black")
    draw_text(screen, f"Brush type: {brush_type_desc[brush_type_idx]}", (left_ui_pos, 200), background_color="black")
    draw_text(screen, f"Brush strength: {brush_sizes[brush_size_idx]}", (left_ui_pos, 230), background_color="black")
    draw_text(screen, f"Tool: {tools_desc[tool]}", (left_ui_pos, 280), color="yellow", background_color="black")
    draw_text(screen, f"Toggle clicking mode: Q - currently {'repeat' if hold_to_place else 'not repeat'}", (left_ui_pos, 310), color="yellow", background_color="black")

    pygame.display.flip()
    pygame.display.set_caption(f"{clock.get_fps():.0f}")

pygame.quit()
