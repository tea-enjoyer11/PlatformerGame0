from typing import Sequence
from enum import Enum, auto
import pygame
import sys
from pygame import Vector2, Surface, Rect, Color
import pygame_gui
import pygame_gui.ui_manager

mainClock = pygame.time.Clock()
pygame.init()
pygame.font.init()
screen = pygame.display.set_mode((800, 600), 0, 32)
font = pygame.font.SysFont("arial", 21)


class TileType(Enum):
    TILE = auto()
    RAMP_LEFT = auto()
    RAMP_RIGHT = auto()


class Tile:
    def __init__(self, color: Color, pos: Vector2, tile_type: TileType = TileType.TILE) -> None:
        if not isinstance(pos, Vector2):
            pos = Vector2(pos)
        self.color = color
        self.pos = pos
        self.type = tile_type


class Ramp(Tile):
    def __init__(self, color: Color, pos: Vector2, tile_type: TileType, elevation: float = 1) -> None:  # angegeben in wie TILESIZE einheit
        super().__init__(color, pos, tile_type)

        self.elevation = elevation


def collision_test(object_1: Rect, object_list: list[Rect]) -> list[Rect]:
    collision_list = []
    for obj in object_list:
        if obj.colliderect(object_1):
            collision_list.append(obj)
    return collision_list


TILESIZE = 50


def tile_rect(t: Tile | Ramp) -> Rect:
    if isinstance(t, Ramp):
        x = t.pos.x * TILESIZE
        y = (t.pos.y * TILESIZE) + TILESIZE - (TILESIZE * t.elevation)
        w = TILESIZE
        h = TILESIZE * t.elevation
        return Rect(x, y, w, h)
    else:  # isinstance(t, Tile)
        return Rect(t.pos.x * TILESIZE, t.pos.y * TILESIZE, TILESIZE, TILESIZE)


def render_collision_mesh(surf: Surface, color: Color, t: Tile | Ramp, width: int = 1) -> None:
    if isinstance(t, Ramp):
        r = tile_rect(t)
        p1, p2 = r.bottomleft, r.topright
        if t.type == TileType.RAMP_LEFT:
            p1, p2 = r.bottomright, r.topleft
        pygame.draw.rect(surf, color, r, width)
        pygame.draw.line(surf, color, p1, p2, width)
    else:  # isinstance(t, Tile)
        r = tile_rect(t)
        pygame.draw.rect(surf, color, r, width)


class Player():
    def __init__(self, pos: Vector2):
        self.pos = pos
        self.color = (0, 0, 255)
        self.rect = Rect(pos.x, pos.y, 25, 50)
        self.vertical_momentum = 0

        self.min_step_height = .5  # in TILESIZE Größe gerechnet

        self._last_pos = Vector2(0)

        self._collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}
        self._last_collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}

    def _is_steppable(self, tile: Rect):
        top_point = tile.y - tile.height
        return top_point - self.pos.y <= self.min_step_height * TILESIZE and self._last_collision_types["bottom"] and (self._last_collision_types["right"] or self._last_collision_types["left"])

    def _is_steppable_ramp(self, ramp: Ramp):
        return TILESIZE * ramp.elevation <= self.min_step_height * TILESIZE

    def move(self, movement: Sequence[float], tiles: list[Tile], dt: float):
        self._last_pos = self.pos.copy()
        self._last_collision_types = self._collision_types.copy()
        normal_tiles = [tile_rect(t) for t in tiles if t.type == TileType.TILE]  # make list of all normal tile rects
        ramps: list[Ramp] = [t for t in tiles if t.type in [TileType.RAMP_LEFT, TileType.RAMP_RIGHT]]  # make list of all ramps

        # handle standard collisions
        collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}
        self.pos[0] += movement[0] * dt
        self.rect.x = int(self.pos[0])
        tile_hit_list = collision_test(self.rect, normal_tiles)
        for t in tile_hit_list:
            if movement[0] > 0:
                self.rect.right = t.left
                collision_types['right'] = True
            elif movement[0] < 0:
                self.rect.left = t.right
                collision_types['left'] = True
            self.pos[0] = self.rect.x
            if self._is_steppable(t):  # das funktioniert nur wenn man an der linken kannte des spielers steht, dann auch nur bis dtmultiplier 2.5, ab 3.0 gehts net mehr TODO: FIXEN
                self.rect.bottom = t.top
                collision_types['bottom'] = True
                self.pos[1] = self.rect.y - 1  # kleiner offset, damit der Spieler nicht an der Kante stecken bleibt
        self.pos[1] += movement[1] * dt
        self.rect.y = int(self.pos[1])
        tile_hit_list = collision_test(self.rect, normal_tiles)
        for t in tile_hit_list:
            if movement[1] > 0:
                self.rect.bottom = t.top
                collision_types['bottom'] = True
            elif movement[1] < 0:
                self.rect.top = t.bottom
                collision_types['top'] = True
            self.pos[1] = self.rect.y

        # handle ramps
        for ramp in ramps:
            hitbox = tile_rect(ramp)
            ramp_collision = self.rect.colliderect(hitbox)

            # TODO: Check einbauen, wo wenn man von der Seite auf die Ramp läuft, wo eigentlich die Wand ist, dass der Spieler da an der Kante hängen bleibt. (später min stepp offset einbauen)

            if ramp_collision:  # check if player collided with the bounding box for the ramp
                # get player's position relative to the ramp on the x axis
                rel_x = self.rect.x - hitbox.x
                max_ramp_height = TILESIZE * ramp.elevation
                ramp_height = 0  # eine Art offset height

                steppable = self._is_steppable_ramp(ramp)

                border_collision_threshold = 5
                if ramp.type == TileType.RAMP_RIGHT:
                    rel_x += self.rect.width
                    ramp_height = rel_x * ramp.elevation

                    # min. stepheight
                    rel_x_border = self.rect.x - (hitbox.x + TILESIZE)  # wie nah ist der Spieler an der Kante?
                    if movement[0] < 0 and (0 < abs(rel_x_border) <= border_collision_threshold) and not steppable:
                        ramp_height = 0
                        self.rect.left = hitbox.right
                        collision_types['left'] = True
                        self.pos[0] = self.rect.x
                elif ramp.type == TileType.RAMP_LEFT:
                    ramp_height = (TILESIZE * ramp.elevation) - rel_x * ramp.elevation

                    # min. stepheight
                    rel_x_border = self.rect.x - hitbox.x + self.rect.width  # wie nah ist der Spieler an der Kante?
                    if movement[0] > 0 and (0 < abs(rel_x_border) <= border_collision_threshold) and not steppable:
                        ramp_height = 0
                        self.rect.right = hitbox.left
                        collision_types['right'] = True
                        self.pos[0] = self.rect.x

                # constraints
                ramp_height = max(0, min(ramp_height, max_ramp_height))

                if 0 <= ramp.elevation <= 1:
                    target_y = hitbox.y + TILESIZE * ramp.elevation - ramp_height
                else:
                    hitbox_bottom_y = hitbox.y + hitbox.height
                    target_y = hitbox_bottom_y - ramp_height

                if self.rect.bottom > target_y:  # check if the player collided with the actual ramp
                    # adjust player height
                    self.rect.bottom = target_y
                    self.pos[1] = self.rect.y

                    collision_types['bottom'] = True

        # return collisions
        self._collision_types = collision_types
        return collision_types


# generate test map
tiles: list[Ramp | Tile] = [Tile("red", Vector2(0, 0)), Ramp('red', Vector2(3, 8), TileType.RAMP_RIGHT), Ramp('red', Vector2(5, 8), TileType.RAMP_RIGHT), Ramp('red', Vector2(7, 8), TileType.RAMP_LEFT, 0.5), Tile('red', Vector2(6, 8)), Tile('red', Vector2(4, 6)), Ramp('red', Vector2(4, 5), TileType.RAMP_LEFT), Tile('red', Vector2(3, 5)), Tile("red", Vector2(11, 8)), Tile("red", Vector2(14, 8)), Tile("red", Vector2(14, 7))]
# tiles: list[Ramp | Tile] = [Ramp("red", Vector2(2, 8), TileType.RAMP_RIGHT, 1), Ramp("red", Vector2(4, 8), TileType.RAMP_LEFT, 1), Ramp("red", Vector2(6, 8), TileType.RAMP_RIGHT, 0.5), Ramp("red", Vector2(8, 8), TileType.RAMP_LEFT, 0.5), Ramp("red", Vector2(10, 8), TileType.RAMP_RIGHT, 2), Ramp("red", Vector2(12, 8), TileType.RAMP_LEFT, 2)]
for i in range(16):
    tiles.append(Tile('red', Vector2(i, 9)))

p = Player(Vector2(200, 500))

right = False
left = False
speed = 200
dt_multiplicator = 1
gravity = 2500
max_gravity = 1000
jumpforce = 700
pygame_gui_manager = pygame_gui.ui_manager.UIManager((800, 600))

gravity_slider = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(210, 500, 500, 30),
                                                        start_value=gravity,
                                                        value_range=(100, 2500),
                                                        manager=pygame_gui_manager)
gravity_textbox = pygame_gui.elements.ui_text_entry_box.UITextEntryBox(pygame.Rect(110, 500, 90, 30),
                                                                       f"{gravity}",
                                                                       manager=pygame_gui_manager)
gravity_lbl = pygame_gui.elements.ui_label.UILabel(pygame.Rect(10, 500, 90, 30),
                                                   "Gravity",
                                                   pygame_gui_manager)
max_gravity_slider = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(210, 530, 500, 30),
                                                            start_value=50,
                                                            value_range=(100, 2500),
                                                            manager=pygame_gui_manager)
max_gravity_lbl = pygame_gui.elements.ui_label.UILabel(pygame.Rect(10, 530, 90, 30),
                                                       "Max. Gravity",
                                                       pygame_gui_manager)
max_gravity_textbox = pygame_gui.elements.ui_text_entry_box.UITextEntryBox(pygame.Rect(110, 530, 90, 30),
                                                                           f"{max_gravity}",
                                                                           manager=pygame_gui_manager)
jumpforce_slider = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(210, 560, 500, 30),
                                                          start_value=jumpforce,
                                                          value_range=(100, 2500),
                                                          manager=pygame_gui_manager)
jumpforce_textbox = pygame_gui.elements.ui_text_entry_box.UITextEntryBox(pygame.Rect(110, 560, 90, 30),
                                                                         f"{jumpforce}",
                                                                         manager=pygame_gui_manager)
jumpforce_lbl = pygame_gui.elements.ui_label.UILabel(pygame.Rect(10, 560, 90, 30),
                                                     "Jumpforce",
                                                     pygame_gui_manager)
# Loop ------------------------------------------------------- #
while True:
    dt = mainClock.tick(0) * 0.001
    dt *= dt_multiplicator

    # Background --------------------------------------------- #
    screen.fill((0, 0, 0))

    # Player ------------------------------------------------- #
    p.vertical_momentum += gravity * dt
    p.vertical_momentum = min(p.vertical_momentum, max_gravity)
    player_movement = [0, p.vertical_momentum]

    if right:
        player_movement[0] += speed
    if left:
        player_movement[0] -= speed

    collisions = p.move(player_movement, tiles, dt)
    if (collisions['bottom']) or (collisions['top']):
        p.vertical_momentum = 0

    pygame.draw.rect(screen, p.color, p.rect)

    # Tiles -------------------------------------------------- #
    for t in tiles:
        color = t.color
        if t.type == TileType.TILE:
            pass
            pygame.draw.rect(screen, color, tile_rect(t))
        elif t.type == TileType.RAMP_RIGHT:
            """Skizze
                          p3
                        / |
                      /   |
                    /     |
                  /       |
                /         |
              /           |
            p1 ---------- p2
            """
            elev = t.elevation
            p1 = Vector2(t.pos.x * TILESIZE, (t.pos.y + 1) * TILESIZE)
            p2 = Vector2((t.pos.x + 1) * TILESIZE, (t.pos.y + 1) * TILESIZE)
            p3 = Vector2((t.pos.x + 1) * TILESIZE, (t.pos.y * TILESIZE) + TILESIZE - (TILESIZE * t.elevation))

            pygame.draw.polygon(screen, color, [p1, p2, p3])

            render_collision_mesh(screen, "white", t, 3)

        elif t.type == TileType.RAMP_LEFT:
            """Skizze
            p3
            | \
            |   \
            |     \
            |       \
            |         \
            |           \
            p1 ---------- p2
            """
            elev = t.elevation
            p1 = Vector2(t.pos.x * TILESIZE, (t.pos.y + 1) * TILESIZE)
            p2 = Vector2((t.pos.x + 1) * TILESIZE - 1, (t.pos.y + 1) * TILESIZE)  # -1 kann man eigentlich weglasse, nur mit siehts schöner aus. Irgendwie ist das ein bisschen länger als TILESIZE
            p3 = Vector2(t.pos.x * TILESIZE, (t.pos.y * TILESIZE) + TILESIZE - (TILESIZE * t.elevation))

            pygame.draw.polygon(screen, color, [p1, p2, p3])

            render_collision_mesh(screen, "white", t, 3)

    cols = font.render(f"{collisions}", True, "white")
    lcols = font.render(f"{p._last_collision_types}", True, "white")
    s = collisions == p._last_collision_types
    cols_same = font.render(f"Are the last and current collisions the same: {s}", True, "white")
    fps_surf = font.render(f"{mainClock.get_fps():.0f}", True, "white")
    dt_surf = font.render(f"DT:{dt:.4f} DT multiplier:{dt_multiplicator:.4f}", True, "white")
    playerinfo_surf = font.render(f"POS:{p.pos}", True, "white")
    screen.blit(cols, (0, 0))
    screen.blit(lcols, (0, 20))
    screen.blit(cols_same, (0, 40))
    screen.blit(dt_surf, (0, 80))
    screen.blit(fps_surf, (600, 0))
    screen.blit(playerinfo_surf, (600, 50))

    # Buttons ------------------------------------------------ #
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            if event.key == pygame.K_d:
                right = True
            if event.key == pygame.K_a:
                left = True
            if event.key == pygame.K_SPACE:
                p.vertical_momentum = -jumpforce
            if event.key == pygame.K_TAB:
                speed = 200 if speed == 200 else 100
            if event.key == pygame.K_UP:
                dt_multiplicator = min(5, dt_multiplicator + 0.5)
            if event.key == pygame.K_DOWN:
                dt_multiplicator = max(0, dt_multiplicator - 0.5)
            if event.key == pygame.K_r:
                p.pos = Vector2(200, 50)
                p.vertical_momentum = 0
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_d:
                right = False
            if event.key == pygame.K_a:
                left = False

        if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if event.ui_element == gravity_slider:
                print('current slider value:', event.value)
                gravity_textbox.set_text(str(event.value))
                gravity = event.value
            elif event.ui_element == max_gravity_slider:
                print('current slider value:', event.value)
                max_gravity_textbox.set_text(str(event.value))
                max_gravity = event.value
            elif event.ui_element == jumpforce_slider:
                print('current slider value:', event.value)
                jumpforce_textbox.set_text(str(event.value))
                jumpforce = event.value

        if event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            if event.ui_element == gravity_textbox:
                print("Changed text:", event.text)
                val = gravity_slider.get_current_value()
                try:
                    val = max(100, min(int(event.text), 1000))
                except ValueError:
                    print(f"Converting error: {event.text=}")
                gravity_slider.set_current_value(val)
                gravity = val
            elif event.ui_element == max_gravity_textbox:
                print("Changed text:", event.text)
                val = max_gravity_slider.get_current_value()
                try:
                    val = max(100, min(int(event.text), 1000))
                except ValueError:
                    print(f"Converting error: {event.text=}")
                max_gravity_slider.set_current_value(val)
                max_gravity = val
            elif event.ui_element == jumpforce_textbox:
                print("Changed text:", event.text)
                val = jumpforce_slider.get_current_value()
                try:
                    val = int(event.text)
                except ValueError:
                    print(f"Converting error: {event.text=}")
                jumpforce_slider.set_current_value(val)
                jumpforce = val

        pygame_gui_manager.process_events(event)

    pygame_gui_manager.update(dt)
    pygame_gui_manager.draw_ui(screen)

    # Update ------------------------------------------------- #
    pygame.display.update()
