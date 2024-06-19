import sys
import pygame_gui
import pygame_gui.ui_manager
import random
import pygame

from Scripts.tiles import *
from Scripts.CONFIG import *
from Scripts.utils import load_image, draw_text, random_color
from Scripts.particles import ParticleGroup, ImageCache, CircleParticle, LeafParticle
from Scripts.entities import Player
from Scripts.timer import TimerManager


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
tile_map = TileMap.deserialize("saves/t1")
tile_map.pre_render_chunks()
global_time = 0

img_cache = ImageCache(load_image)
particle_group = ParticleGroup(img_cache)


# loading grass blade images
for f in os.listdir("assets/tiles/grass_blades"):
    GrassBlade.img_cache[f"{f.split('.')[0]};{0}"] = load_image(f"assets/tiles/grass_blades/{f}")
    GrassBlade.offset_cache[f"{f.split('.')[0]};{0}"] = Vector2(0, 0)
grass_blades = []
# testing grass blades
for i in range(100):
    gb = GrassBlade(Vector2(2 + i / 4, 20), random.randint(0, 6))
    tile_map.add_offgrid(gb)
    grass_blades.append(gb)
tile_map.pre_render_chunks()

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
    dt = mainClock.tick(fps_options[fps_idx]) * 0.001 * dt_multiplicator
    global_time += dt

    [b.update(global_time) for b in grass_blades]
    tile_map.pre_render_chunks()  # TODO besseren weg finden alle grass blades zu updated ohne ALLE chunks zu prerendern

    # self.scroll += ((self.player.pos - Vector2(4, 4)) - RES / 4 / 2 - self.scroll) / 30
    scroll += ((p.pos - Vector2(TILESIZE / 2)) - DOWNSCALED_RES / 2 - scroll) / 30

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

    master_screen.blit(pygame.transform.scale(screen, RES), (0, 0))

    draw_text(master_screen, f"DT: {dt:.6f} DT multiplier:{dt_multiplicator:.4f}", (0, 80), outline_color="black")
    draw_text(master_screen, f"{mainClock.get_fps():.0f}", (500, 0), outline_color="black")
    draw_text(master_screen, f"{player_movement[0]:.2f}, {player_movement[1]:.2f}", (0, 200), outline_color="black")
    draw_text(master_screen, f"TILEPOS: {p.pos // TILESIZE}\nPOS:{p.pos}\nNOCLIP: {noclip}", (500, 50), outline_color="black")
    draw_text(master_screen, f"TILEMAP:\nAmount of Chunks: {len(tile_map._chunks)}\nAmount of Tiles: {tile_map.amount_of_tiles}", (500, 150), outline_color="black")
    draw_text(master_screen, f"PARTICLES:\nAmount of Particles: {len(particle_group)}", (500, 250), outline_color="black")
    draw_text(master_screen, f"{collisions}", (0, 0), font=font, outline_color="black")
    draw_text(master_screen, f"{p._last_collision_types}", (0, 20), outline_color="black")
    draw_text(master_screen, f"Are the last and current collisions the same: {collisions == p._last_collision_types}", (0, 40), outline_color="black")

    pygame.display.flip()

pygame.quit()
sys.exit()
