import sys
import pygame_gui
import pygame_gui.ui_manager
import random
import pygame
import os

from Scripts.tiles import *
from Scripts.CONFIG import *
from Scripts.utils import load_image, draw_text, random_color, make_surface
from Scripts.particles import ParticleGroup, ImageCache, CircleParticle, LeafParticle
from Scripts.timer import TimerManager

from Scripts.entities import Transform, Image, ImageRenderer, Velocity, PhysicsMovementSystem, CollisionResolver
import Scripts.Ecs as Ecs
# p = Player(Vector2(200, 500))

os.environ['SDL_VIDEO_CENTERED'] = '1'

# loading grass blade images
for f in os.listdir("assets/tiles/grass_blades"):
    GrassBlade.img_cache[f"{f.split('.')[0]};{0}"] = load_image(f"assets/tiles/grass_blades/{f}")
    GrassBlade.offset_cache[f"{f.split('.')[0]};{0}"] = Vector2(0, 0)
    GrassBlade.img_half_size_cache[f"{f.split('.')[0]};{0}"] = tuple(Vector2(load_image(f"assets/tiles/grass_blades/{f}").get_size()) // 2)

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
jumpforce = 470
noclip = True
scroll = Vector2(0)
pygame_gui_manager = pygame_gui.ui_manager.UIManager((800, 600))
tile_map = TileMap()
tile_map = TileMap.deserialize("saves/t1")
tile_map.pre_render_chunks()
global_time = 0

img_cache = ImageCache(load_image)
particle_group = ParticleGroup(img_cache)

component_manager = Ecs.ComponentManager()
entity_manager = Ecs.EntityManager(component_manager)
system_manager = Ecs.SystemManager(entity_manager, component_manager)

p = entity_manager.add_entity()
component_manager.add_component(p, [
    Transform(200, 30, 8, 16),
    Image(make_surface((8, 16), color=(255, 255, 125))),
    Velocity(1, 1)])
renderer_sys = ImageRenderer(screen)
movement_sys = PhysicsMovementSystem()
collision_resolver_sys = CollisionResolver()
system_manager.add_system(p, renderer_sys)
system_manager.add_system(p, movement_sys)
system_manager.add_system(p, collision_resolver_sys)

# grass_blades = []
# # testing grass blades
# for i in range(100):
#     gb = GrassBlade(Vector2(2 + i / 4, 20), random.randint(0, 6))
#     tile_map.add_offgrid(gb)
#     grass_blades.append(gb)

# region Slider setup
gravity_slider = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(210, 500, 500, 30),
                                                        start_value=gravity,
                                                        value_range=(1, 2500),
                                                        manager=pygame_gui_manager)
gravity_textbox = pygame_gui.elements.ui_text_entry_box.UITextEntryBox(pygame.Rect(110, 500, 90, 30),
                                                                       f"{gravity}",
                                                                       manager=pygame_gui_manager)
gravity_lbl = pygame_gui.elements.ui_label.UILabel(pygame.Rect(10, 500, 90, 30),
                                                   "Gravity",
                                                   pygame_gui_manager)
max_gravity_slider = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(210, 530, 500, 30),
                                                            start_value=max_gravity,
                                                            value_range=(1, 2500),
                                                            manager=pygame_gui_manager)
max_gravity_lbl = pygame_gui.elements.ui_label.UILabel(pygame.Rect(10, 530, 90, 30),
                                                       "Max. Gravity",
                                                       pygame_gui_manager)
max_gravity_textbox = pygame_gui.elements.ui_text_entry_box.UITextEntryBox(pygame.Rect(110, 530, 90, 30),
                                                                           f"{max_gravity}",
                                                                           manager=pygame_gui_manager)
jumpforce_slider = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(210, 560, 500, 30),
                                                          start_value=jumpforce,
                                                          value_range=(1, 2500),
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
    def rot_function(x): return int(math.sin(global_time * 100 / 60 + x / 100) * 25)
    GrassBlade.rot_function = rot_function

    [b.update(global_time) for b in tile_map.get_all_offgrid()]
    tile_map.pre_render_chunks()  # TODO besseren weg finden alle grass blades zu updated ohne ALLE chunks zu prerendern

    # self.scroll += ((self.player.pos - Vector2(4, 4)) - RES / 4 / 2 - self.scroll) / 30
    # scroll += ((p.pos - Vector2(TILESIZE / 2)) - DOWNSCALED_RES / 2 - scroll) / 30
    scroll += ((component_manager.get_component(p, Transform).pos - Vector2(TILESIZE / 2)) - DOWNSCALED_RES / 2 - scroll) / 30

    # Background --------------------------------------------- #
    screen.fill((0, 0, 0))

    # Player ------------------------------------------------- #
    p_velocity = component_manager.get_component(p, Velocity)
    if not noclip:
        vel = component_manager.get_component(p, Velocity)
        vel.y += gravity * dt
        vel.y = min(vel.y, max_gravity)
        # print(vel.y, max_gravity)
        # player_movement = [0, vel.y]
        player_movement[1] = vel.y
        player_movement[0] = 0
    if right:
        player_movement[0] = speed
        p_velocity.x = 1
    elif left:
        player_movement[0] = speed
        p_velocity.x = -1
    else:
        player_movement[0] = 0
    if noclip:
        player_movement[1] = 0
        if up:
            player_movement[1] = speed
            p_velocity.y = -1
        if down:
            player_movement[1] = speed
            p_velocity.y = 1

    if boost:
        player_movement[0] *= 4
        player_movement[1] *= 4

    # close_tiles = tile_map.get_around(p.pos)
    # collisions = p.move(player_movement, close_tiles, dt, noclip)
    # if (collisions['bottom']) or (collisions['top']) and not noclip:
    #     p.vel.y = 0

    timermanager.update()
    # p.update(dt)

    tile_map.render(screen, component_manager.get_component(p, Transform).pos, offset=scroll)
    # pygame.draw.rect(screen, "blue", Rect(Vector2(component_manager.get_component(p, Transform).rect.topleft) - scroll, component_manager.get_component(p, Transform).rect.size))
    system_args = {"scroll": scroll, "movement": player_movement, "dt": dt, "tilemap": tile_map, "noclip": noclip, "gravity": gravity, "max_gravity": max_gravity}
    # system_manager.run_all_systems(**system_args)
    system_manager.run_base_system(collision_resolver_sys, **system_args)
    system_manager.run_base_system(movement_sys, **system_args)
    system_manager.run_base_system(renderer_sys, **system_args)

    # p.render(screen, scroll)

    # for tile in close_tiles:
    #     render_collision_mesh(screen, "yellow", tile, offset=scroll)

    # region Events
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
                p_velocity = component_manager.get_component(p, Velocity)
                p_velocity.y = -jumpforce
                # p.set_state("jump_init")
                print(component_manager.get_component(p, Velocity).xy)
            if event.key == pygame.K_TAB:
                noclip = not noclip
                p_velocity = component_manager.get_component(p, Velocity)
                p_velocity.y = 0
            if event.key == pygame.K_UP:
                dt_multiplicator = min(5, dt_multiplicator + 0.25)
            if event.key == pygame.K_DOWN:
                dt_multiplicator = max(0, dt_multiplicator - 0.25)
            if event.key == pygame.K_r:
                p_transform = component_manager.get_component(p, Transform)
                p_transform.pos = Vector2(200, 50)
                p_velocity = component_manager.get_component(p, Velocity)
                p_velocity.y = 0
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
                    val = max(gravity_slider.value_range[0], min(int(event.text), gravity_slider.value_range[1]))
                    gravity_slider.set_current_value(val)
                    gravity = val
                except ValueError:
                    print(f"Converting error: {event.text=}")
            elif event.ui_element == max_gravity_textbox:
                print("Changed text:", event.text)
                val = max_gravity_slider.get_current_value()
                try:
                    val = max(max_gravity_slider.value_range[0], min(int(event.text), max_gravity_slider.value_range[0]))
                    max_gravity_slider.set_current_value(val)
                    max_gravity = val
                except ValueError:
                    print(f"Converting error: {event.text=}")
            elif event.ui_element == jumpforce_textbox:
                print("Changed text:", event.text)
                val = jumpforce_slider.get_current_value()
                try:
                    val = max(jumpforce_slider.value_range[0], min(int(event.text), jumpforce_slider.value_range[0]))
                    jumpforce_slider.set_current_value(val)
                    jumpforce = val
                except ValueError:
                    print(f"Converting error: {event.text=}")
        # endregion

        pygame_gui_manager.process_events(event)
    # endregion

    m_pos = tuple(pygame.Vector2(pygame.mouse.get_pos()))
    if pygame.mouse.get_pressed()[0]:
        particle_group.add([CircleParticle(m_pos, (random.randrange(-100, 100), random.randrange(-100, 100)), 4, type="particle") for _ in range(5)])
    if pygame.mouse.get_pressed()[2]:
        particle_group.add([LeafParticle(m_pos, (random.randrange(-30, 30), random.randrange(-30, 30)), 18, type="leaf") for _ in range(5)])

    particle_group.update(dt)
    particle_group.draw(screen, blend=pygame.BLEND_RGB_ADD)

    pygame_gui_manager.update(dt)

    master_screen.blit(pygame.transform.scale(screen, RES), (0, 0))

    outline_color = None
    p_transform = component_manager.get_component(p, Transform)
    draw_text(master_screen, f"DT: {dt:.6f} DT multiplier:{dt_multiplicator:.4f}", (0, 80), outline_color=outline_color)
    draw_text(master_screen, f"{mainClock.get_fps():.0f}", (500, 0), outline_color=outline_color)
    draw_text(master_screen, f"{player_movement[0]:.2f}, {player_movement[1]:.2f}", (0, 200), outline_color=outline_color)
    draw_text(master_screen, f"TILEPOS: {p_transform.pos // TILESIZE}\nPOS:{p_transform.pos}\nNOCLIP: {noclip}", (500, 50), outline_color=outline_color)
    draw_text(master_screen, f"TILEMAP:\nAmount of Chunks: {len(tile_map._chunks)}\nAmount of Tiles: {tile_map.amount_of_tiles}", (500, 150), outline_color=outline_color)
    draw_text(master_screen, f"PARTICLES:\nAmount of Particles: {len(particle_group)}", (500, 250), outline_color=outline_color)
    # draw_text(master_screen, f"{collisions}", (0, 0), font=font, outline_color=outline_color)
    # draw_text(master_screen, f"{p._last_collision_types}", (0, 20), outline_color=outline_color)
    # draw_text(master_screen, f"Are the last and current collisions the same: {collisions == p._last_collision_types}", (0, 40), outline_color=outline_color)

    pygame_gui_manager.draw_ui(master_screen)

    pygame.display.flip()

pygame.quit()
sys.exit()
