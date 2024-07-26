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


RES = Vector2(1200, 700)
left_menu_offset = 500
tile_displaying_offset = 4
timermanager = TimerManager()


class LevelEditor:
    def __init__(self) -> None:
        self.screen = pygame.display.set_mode(RES, 0, 32)
        self.clock = pygame.time.Clock()
        self.offset = Vector2(0)
        self.mPos = Vector2(0)
        self.highlight_tile_pos = Vector2(0)
        self.x_off = 0
        self.y_off = 0
        self.tilemap = TileMap()
        self.tile_position = Vector2(0)
        self.sub_tile_position = Vector2(0)

        self.mode = 0
        self.modes = [0, 1]
        self.modes_desc = ["tile placing", "pixel placing"]

        self.brush_size = 0
        self.brush_size_idx = 0
        self.brush_sizes = [0, 1, 2, 3, 4, 5]
        self.brush_type = 0
        self.brush_types = [0, 1]  # 0=circle, 1=square
        self.brush_type_idx = 0
        self.brush_type_desc = ["circle", "square"]

        self.tool = 0
        self.tools = [0, 1]
        self.tools_desc = ["brush", "rect"]

        self.rect_tool_start: Vector2 = None
        self.rect_tool_end: Vector2 = None
        self.do_rect_tool = False

        self.selected_tile = (0, 0)
        self.hold_to_place = True

        self.clicks = [False, False, False]
        self.last_mClicks = (False, False, False)
        self.click_timer = Timer(0.1, True, True)

        # tile set
        self.tiles = parse_master_tile_set("assets/tileset template.png")

        for f in os.listdir("assets/tiles/grass_blades"):
            GrassBlade.img_cache[f"{f.split('.')[0]};{0}"] = load_image(f"assets/tiles/grass_blades/{f}")
            GrassBlade.offset_cache[f"{f.split('.')[0]};{0}"] = Vector2(0, 0)
            GrassBlade.img_half_size_cache[f"{f.split('.')[0]};{0}"] = tuple(Vector2(load_image(f"assets/tiles/grass_blades/{f}").get_size()) // 2)

        self.dt = .0

    def get_positions(self) -> list[Vector2]:
        positions = []
        center = self.tile_position

        if self.brush_type == 0:  # circle:
            for y in range(-self.brush_size, self.brush_size + 1):
                for x in range(-self.brush_size, self.brush_size + 1):
                    pos = Vector2(center.x + x, center.y + y)
                    distance = (pos - center).length()
                    if distance <= self.brush_size:
                        positions.append(pos)
        elif self.brush_type == 1:  # square
            for y in range(-self.brush_size, self.brush_size + 1):
                for x in range(-self.brush_size, self.brush_size + 1):
                    pos = Vector2(center.x + x, center.y + y)
                    positions.append(pos)

        return positions

    def run(self):
        run = True
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    run = False
                    break
                self.handle_event(event)

            self.update()

            self.render()
        pygame.quit()

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.offset = Vector2(0)
            if event.key == pygame.K_t:
                self.tool = (self.tool + 1) % len(self.tools)
            if event.key == pygame.K_o:
                save()
            if event.key == pygame.K_i:
                self.tilemap = load()
            if event.key == pygame.K_u:
                backup()
            if event.key == pygame.K_g:
                mode = (mode + 1) % len(self.modes)
            if event.key == pygame.K_h:
                self.brush_size_idx = (self.brush_size_idx + 1) % len(self.brush_sizes)
                self.brush_size = self.brush_sizes[self.brush_size_idx]
            if event.key == pygame.K_j:
                self.brush_type_idx = (self.brush_type_idx + 1) % len(self.brush_types)
                self.brush_type = self.brush_types[self.brush_type_idx]
            if event.key == pygame.K_q:
                self.hold_to_place = not self.hold_to_place

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.tool == 1:  # rect tool
                self.rect_tool_start = self.mPos + self.offset
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.tool == 1:  # rect tool
                self.rect_tool_end = self.mPos
                self.do_rect_tool = True

    def update(self):
        self.last_mClicks = self.clicks
        self.clicks = self.get_mouse_pressed()
        self.dt = self.clock.tick(0)

        if self.rect_tool_start and not self.do_rect_tool:
            self.rect_tool_end = self.mPos

        keys = pygame.key.get_pressed()
        self.last_mPos = self.mPos.copy()
        self.mPos = Vector2(pygame.mouse.get_pos())
        self.tile_position = Vector2(int((self.mPos[0] + self.offset.x) // TILESIZE), int((self.mPos[1] + self.offset.y) // TILESIZE))
        self.sub_tile_position = self.mPos + self.offset - self.tile_position * TILESIZE

        up = keys[pygame.K_w]
        left = keys[pygame.K_a]
        down = keys[pygame.K_s]
        right = keys[pygame.K_d]
        ctrl = keys[pygame.K_LCTRL]

        self.x_off = self.offset.x % TILESIZE
        self.y_off = self.offset.y % TILESIZE

        if up:
            self.offset.y -= 2 * (1 + int(ctrl) * 4) * 1 / 4 * self.dt
        if down:
            self.offset.y += 2 * (1 + int(ctrl) * 4) * 1 / 4 * self.dt
        if left:
            self.offset.x -= 2 * (1 + int(ctrl) * 4) * 1 / 4 * self.dt
        if right:
            self.offset.x += 2 * (1 + int(ctrl) * 4) * 1 / 4 * self.dt

        if self.clicks[0] and self.click_timer:
            if self.mPos.x < left_menu_offset:  # menu
                p = self.mPos // (TILESIZE + tile_displaying_offset)
                if p.y < len(self.tiles) and p.x < len(self.tiles[0]):
                    selected_tile = (
                        clamp(0, int(p.y), len(self.tiles) - 1),
                        clamp(0, int(p.x), len(self.tiles[0]) - 1)
                    )
            else:  # tile placing
                if self.tool == 0:
                    if self.mode == 0:
                        offgrid = False
                        for position in self.get_positions():
                            idx = f"c_tile({self.selected_tile[1]};{self.selected_tile[0]})"
                            if self.selected_tile in [(14, 0), (14, 1), (14, 2), (15, 0), (15, 1), (15, 2), (16, 0), (16, 1), (16, 2)]:
                                t = Tile(position, img_idx=f"TEST{idx}")
                            elif self.selected_tile in [(14, 3), (14, 4), (14, 5), (14, 6), (14, 7), (14, 8), (14, 9)]:
                                img_idx = f"{self.selected_tile[1]-3}"
                                p = self.mPos - Vector2(GrassBlade.img_cache[f"{img_idx};0"].get_size()) / 2
                                t = GrassBlade((p + self.offset) / TILESIZE, img_idx=img_idx)
                                t.img_idx = f"{img_idx};0"
                                offgrid = True
                                print(self.selected_tile, img_idx, t.img_idx)
                            else:
                                t = CustomTile(position, idx, idx)
                            if offgrid:
                                self.tilemap.add_offgrid(t)
                            else:
                                self.tilemap.add(t)
                        self.tilemap.pre_render_chunks()
                    elif self.mode == 1:
                        pass
        if self.clicks[2]:
            if self.mPos.x < left_menu_offset:
                ...
            else:
                if self.tool == 0:
                    if self.mode == 0:
                        offgrid = False
                        for position in self.get_positions():
                            if self.selected_tile in [(14, 3), (14, 4), (14, 5), (14, 6), (14, 7), (14, 8), (14, 9)]:
                                offgrid = True
                            if offgrid:
                                img_idx = f"{self.selected_tile[1]-3}"
                                p = self.mPos - Vector2(GrassBlade.img_cache[f"{img_idx};0"].get_size()) / 2
                                self.tilemap.remove_offgrid((p + self.offset) / TILESIZE)
                            else:
                                self.tilemap.remove(position)
                        self.tilemap.pre_render_chunks()

        if self.do_rect_tool:
            print(self.rect_tool_start, self.rect_tool_end)

            self.tile_pos_start = self.rect_tool_start // TILESIZE
            self.tile_pos_end = (self.rect_tool_end + self.offset) // TILESIZE

            # ...

            print(self.tile_pos_start, self.tile_pos_end)

            self.rect_tool_start = None
            self.rect_tool_end = None
            self.do_rect_tool = False

    def render_grid(self):
        for y in range(-TILESIZE, int(RES.y) + TILESIZE, TILESIZE):
            for x in range(left_menu_offset - TILESIZE, int(RES.x) + TILESIZE, TILESIZE):
                p = Vector2(x - self.x_off, y - self.y_off)
                rect = pygame.Rect(p.x - 4, p.y, TILESIZE, TILESIZE)

                pygame.draw.rect(self.screen, "white", rect, 1)

    def render_selected_tile(self):
        if self.mPos.x > left_menu_offset:
            pygame.draw.rect(self.screen, "yellow", [self.tile_position.x * TILESIZE - self.offset.x, self.tile_position.y * TILESIZE - self.offset.y, TILESIZE, TILESIZE], 1)

    def render_ui(self):
        # display tiles & current tile
        pygame.draw.rect(self.screen, (70, 0, 70), Rect(0, 0, left_menu_offset, RES.y))  # left ui panel background
        for y, row in enumerate(self.tiles):
            for x, surf in enumerate(row):
                p = Vector2(x * TILESIZE, y * TILESIZE)
                p += Vector2(tile_displaying_offset * x, tile_displaying_offset * y)
                self.screen.blit(surf, p)
        pygame.draw.rect(
            self.screen,
            "red",
            Rect(
                self.selected_tile[1] * (TILESIZE + tile_displaying_offset) - tile_displaying_offset / 2,
                self.selected_tile[0] * (TILESIZE + tile_displaying_offset) - tile_displaying_offset / 2,
                TILESIZE + tile_displaying_offset,
                TILESIZE + tile_displaying_offset
            ),
            int(tile_displaying_offset / 2)
        )

        left_ui_pos = left_menu_offset + 10
        right_ui_pos = RES.x - 300
        self.screen.blit(pygame.transform.scale(self.tiles[self.selected_tile[0]][self.selected_tile[1]], (80, 80)), (left_ui_pos - 100, 20))
        draw_text(self.screen, f"Load with 'I' | Save wiht 'O'", (right_ui_pos, 10), color="yellow", background_color="black")
        draw_text(self.screen, f"Cycle placing modes with 'G'", (right_ui_pos, 40), color="yellow", background_color="black")
        draw_text(self.screen, f"Cycle brush sizes with 'H'", (right_ui_pos, 70), color="yellow", background_color="black")
        draw_text(self.screen, f"Cycle brush types with 'J'", (right_ui_pos, 100), color="yellow", background_color="black")
        draw_text(self.screen, f"Cycle tools with 'T'", (right_ui_pos, 130), color="yellow", background_color="black")
        draw_text(self.screen, f"Num Tiles: {self.tilemap.amount_of_tiles} | Num Chunks: {self.tilemap.amount_of_chunks}", (left_ui_pos, 10), background_color="black")
        draw_text(self.screen, f"Offset: {self.offset}", (left_ui_pos, 40), background_color="black")
        draw_text(self.screen, f"Tile Offset: {Vector2(self.x_off, self.y_off)}", (left_ui_pos, 70), background_color="black")
        draw_text(self.screen, f"TILEPOS: {self.tile_position} SUBTILEPOS: {self.sub_tile_position} CHUNKPOS: {self.mPos//CHUNKSIZE}", (left_ui_pos, 110), background_color="black")
        draw_text(self.screen, f"Mode: {self.modes_desc[self.mode]}", (left_ui_pos, 140), background_color="black")
        draw_text(self.screen, f"Brush type: {self.brush_type_desc[self.brush_type_idx]}", (left_ui_pos, 200), background_color="black")
        draw_text(self.screen, f"Brush strength: {self.brush_sizes[self.brush_size_idx]}", (left_ui_pos, 230), background_color="black")
        draw_text(self.screen, f"Tool: {self.tools_desc[self.tool]}", (left_ui_pos, 280), color="yellow", background_color="black")
        draw_text(self.screen, f"Toggle clicking mode: Q - currently {'repeat' if self.hold_to_place else 'not repeat'}", (left_ui_pos, 310), color="yellow", background_color="black")

    def render(self):
        self.screen.fill((92, 95, 89))
        self.render_grid()
        self.tilemap.render(self.screen, self.mPos + self.offset, offset=self.offset)  # TODO so was wie: culling_rect=Rect(left_menu_offset, 0, RES.x - left_menu_offset, RES.y) einbauen
        self.render_selected_tile()

        # rect tool
        if self.rect_tool_start:
            # inversing rect sodass auch links und nach oben gezogen werden kann
            x = self.rect_tool_start.x - self.offset.x
            y = self.rect_tool_start.y - self.offset.y
            w = self.rect_tool_end.x - self.rect_tool_start.x + self.offset.x
            h = self.rect_tool_end.y - self.rect_tool_start.y + self.offset.y
            r = Rect(x, y, w, h)
            print(r)
            pygame.draw.rect(screen, "yellow", r, 2)

        self.render_ui()

        pygame.display.set_caption(f"{self.clock.get_fps():.0f}")

        pygame.display.flip()

    def get_mouse_pressed(self) -> tuple[bool, bool, bool]:
        if self.hold_to_place:
            return pygame.mouse.get_pressed()

        a = pygame.mouse.get_pressed()
        ret = [False, False, False]
        for i, v in enumerate(a):
            if not self.last_mClicks[i]:
                ret[i] = a[i]

        return tuple(ret)


if __name__ == "__main__":
    LevelEditor().run()
