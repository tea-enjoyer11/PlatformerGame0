import sys
import pygame_gui
import pygame_gui.ui_manager
import random
import pygame

from Scripts.tiles import *
from Scripts.CONFIG import *
from Scripts.utils import load_image, draw_text
from Scripts.particles import ParticleGroup, ImageCache, CircleParticle, LeafParticle
from Scripts.entities import Player
from Scripts.timer import TimerManager

# generate test map
# tiles: list[Ramp | Tile] = [Tile(Vector2(0, 0)), Ramp('red', Vector2(3, 8), TileType.RAMP_RIGHT), Ramp('red', Vector2(5, 8), TileType.RAMP_RIGHT), Ramp('red', Vector2(7, 8), TileType.RAMP_LEFT, 0.5), Tile('red', Vector2(6, 8)), Tile('red', Vector2(4, 6)), Ramp('red', Vector2(4, 5), TileType.RAMP_LEFT), Tile('red', Vector2(3, 5)), Tile(Vector2(11, 8)), Tile(Vector2(14, 8)), Tile(Vector2(14, 7))]
tiles: list[Ramp | Tile] = [Ramp(Vector2(2, 8), TileType.RAMP_RIGHT, 1), Ramp(Vector2(4, 8), TileType.RAMP_LEFT, 1), Ramp(Vector2(6, 8), TileType.RAMP_RIGHT, 0.5), Ramp(Vector2(8, 8), TileType.RAMP_LEFT, 0.5), Ramp(Vector2(10, 8), TileType.RAMP_RIGHT, 2), Ramp(Vector2(12, 8), TileType.RAMP_LEFT, 2)]
for i in range(16):
    tiles.append(Tile(Vector2(i, 9)))
# tiles = []
for i in range(CHUNKSIZE):
    tiles.append(Tile(Vector2(0, i)))
tiles.append(CustomRamp(Vector2(-1, 9), load_image("assets/custom_ramp_hitbox.png"), TileType.RAMP_RIGHT, img_idx=3))
tiles.append(CustomRamp(Vector2(-3, 9), load_image("assets/custom_ramp2_hitbox.png"), TileType.RAMP_LEFT, img_idx=4))
tiles.append(CustomRamp(Vector2(-4, 9), load_image("assets/custom_ramp2_hitbox.png", flip_x=True), TileType.RAMP_RIGHT, img_idx=44))
tiles.append(CustomRamp(Vector2(-7, 9), load_image("assets/custom_ramp3_hitbox.png"), TileType.RAMP_RIGHT, img_idx=5))
tiles.append(CustomRamp(Vector2(-6, 9), load_image("assets/custom_ramp3_hitbox.png", flip_x=True), TileType.RAMP_LEFT, img_idx=55))
tiles.append(CustomRamp(Vector2(-11, 9), load_image("assets/custom_ramp_hitbox.png"), TileType.RAMP_RIGHT, img_idx=3))
tiles.append(CustomRamp(Vector2(-10, 9), load_image("assets/custom_ramp_hitbox.png", flip_x=True), TileType.RAMP_LEFT, img_idx=33))
tiles.append(CustomRamp(Vector2(-13, 9), load_image("assets/custom_ramp3_hitbox.png", flip_x=True), TileType.RAMP_LEFT, img_idx=55))
tiles.append(CustomRamp(Vector2(-15, 9), load_image("assets/custom_ramp3_hitbox.png"), TileType.RAMP_RIGHT, img_idx=5))
custom_tile = CustomTile(Vector2(-21, 9))
custom_tile.extend_pixels([(i, 15) for i in range(TILESIZE - 1)])
custom_tile.pre_render()
tiles.append(custom_tile)
for x in range(-24, 24):
    for y in range(16):
        tiles.append(Tile(Vector2(x, 10 + y)))
p = Player(Vector2(200, 500))


timermanager = TimerManager()
right = False
left = False
up = False
down = False
boost = False
speed = 200
dt_multiplicator = 1
gravity = 2500
max_gravity = 1000
jumpforce = 700
noclip = False
scroll = Vector2(0)
pygame_gui_manager = pygame_gui.ui_manager.UIManager((800, 600))
tile_map = TileMap()
# tile_map.extend(tiles)
tile_map = TileMap.deserialize("saves/t1")
tile_map.pre_render_chunks()

img_cache = ImageCache(load_image)
particle_group = ParticleGroup(img_cache)
# renderer = Renderer()

# region Slider setup
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
                                                            start_value=max_gravity,
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
# endregion

# Loop ------------------------------------------------------- #
player_movement = [0, 0]
fps_options = [0, 15, 30, 60, 120, 240]
fps_idx = 0
run = True
while run:
    dt = mainClock.tick(fps_options[fps_idx]) * 0.001
    dt *= dt_multiplicator

    # self.scroll += ((self.player.pos - Vector2(4, 4)) - RES / 4 / 2 - self.scroll) / 30
    scroll += ((p.pos - Vector2(TILESIZE / 2)) - RES / 2 - scroll) / 30

    # Background --------------------------------------------- #
    screen.fill((0, 0, 0))

    # Player ------------------------------------------------- #
    if not noclip:
        p.vel.y += gravity * dt
        p.vel.y = min(p.vel.y, max_gravity)
        # player_movement = [0, p.vel.y]
        player_movement[1] = p.vel.y
        player_movement[0] = 0
    if noclip:
        player_movement = [0, 0]

    if right:
        player_movement[0] += speed
    if left:
        player_movement[0] -= speed
    if noclip:
        if up:
            player_movement[1] -= speed
        if down:
            player_movement[1] += speed

    if boost:
        player_movement[0] *= 4
        player_movement[1] *= 4

    close_tiles = tile_map.get_around(p.pos)
    collisions = p.move(player_movement, close_tiles, dt, noclip)
    if (collisions['bottom']) or (collisions['top']) and not noclip:
        p.vel.y = 0

    timermanager.update()
    p.update(dt)

    tile_map.render(screen, p.pos, offset=scroll)
    pygame.draw.rect(screen, "blue", Rect(Vector2(p.rect.topleft) - scroll, p.rect.size))
    p.render(screen, scroll)

    for tile in close_tiles:
        render_collision_mesh(screen, "yellow", tile, offset=scroll)

    draw_text(screen, f"DT:{dt:.4f} DT multiplier:{dt_multiplicator:.4f}", (0, 80))
    draw_text(screen, f"{mainClock.get_fps():.0f}", (500, 0))
    draw_text(screen, f"{player_movement[0]:.2f}, {player_movement[1]:.2f}", (0, 200))
    draw_text(screen, f"TILEPOS: {p.pos // TILESIZE}\nPOS:{p.pos}\nNOCLIP: {noclip}", (500, 50))
    draw_text(screen, f"TILEMAP:\nAmount of Chunks: {len(tile_map._chunks)}\nAmount of Tiles: {tile_map.amount_of_tiles}", (500, 150))
    draw_text(screen, f"PARTICLES:\nAmount of Particles: {len(particle_group)}", (500, 250))
    draw_text(screen, f"{collisions}", (0, 0), font=font)
    draw_text(screen, f"{p._last_collision_types}", (0, 20))
    draw_text(screen, f"Are the last and current collisions the same: {collisions == p._last_collision_types}", (0, 40))

    # Buttons ------------------------------------------------ #
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                right = True
            if event.key == pygame.K_a:
                left = True
            if event.key == pygame.K_w:
                up = True
            if event.key == pygame.K_s:
                down = True
            if event.key == pygame.K_SPACE:
                p.vel.y = -jumpforce
                p.set_state("jump_init")
            if event.key == pygame.K_TAB:
                noclip = not noclip
                p.vel.y = 0
            if event.key == pygame.K_UP:
                dt_multiplicator = min(5, dt_multiplicator + 0.25)
            if event.key == pygame.K_DOWN:
                dt_multiplicator = max(0, dt_multiplicator - 0.25)
            if event.key == pygame.K_r:
                p.pos = Vector2(200, 50)
                p.vel.y = 0
                particle_group.clear()
            if event.key == pygame.K_LCTRL:
                boost = True
            if event.key == pygame.K_g:
                fps_idx = (fps_idx + 1) % len(fps_options)
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_d:
                right = False
            if event.key == pygame.K_a:
                left = False
            if event.key == pygame.K_w:
                up = False
            if event.key == pygame.K_s:
                down = False
            if event.key == pygame.K_LCTRL:
                boost = False

        # region ui events
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
        # endregion

        pygame_gui_manager.process_events(event)

    m_pos = tuple(pygame.Vector2(pygame.mouse.get_pos()))
    if pygame.mouse.get_pressed()[0]:
        particle_group.add([CircleParticle(m_pos, (random.randrange(-100, 100), random.randrange(-100, 100)), 4, type="particle") for _ in range(5)])
    if pygame.mouse.get_pressed()[2]:
        particle_group.add([LeafParticle(m_pos, (random.randrange(-30, 30), random.randrange(-30, 30)), 18, type="leaf") for _ in range(5)])

    particle_group.update(dt)
    particle_group.draw(screen, blend=pygame.BLEND_RGB_ADD)

    pygame_gui_manager.update(dt)
    pygame_gui_manager.draw_ui(screen)

    # Update ------------------------------------------------- #
    # renderer.render(screen)
    # renderer.render_particles(particle_group.particles)
    pygame.display.flip()
# renderer.quit()
pygame.quit()
sys.exit()
