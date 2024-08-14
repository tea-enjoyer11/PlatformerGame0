import sys
import pygame_gui
import pygame_gui.ui_manager
import random
import pygame
import os

from Scripts.tilemap import TileMap
from Scripts.CONFIG import *
from Scripts.utils import load_image, draw_text, random_color, make_surface, load_images
from Scripts.particles import ParticleGroup, ImageCache, CircleParticle, LeafParticle
from Scripts.timer import TimerManager

from Scripts.entities import Transform, Image, ImageRenderer, Velocity, CollisionResolver, Animation, AnimationRenderer, AnimationUpdater
import Scripts.Ecs as Ecs

os.environ['SDL_VIDEO_CENTERED'] = '1'


class Game:
    def __init__(self) -> None:
        self.timermanager = TimerManager()
        self.dt_multiplicator = 1
        self.gravity = 6
        self.max_gravity = 700
        self.jumpforce = 600
        self.noclip = True
        self.scroll = Vector2(0)
        self.pygame_gui_manager = pygame_gui.ui_manager.UIManager((800, 600))
        self.tile_map = TileMap(self)
        self.tile_map.load("map.json")

        self.img_cache = ImageCache(load_image)
        self.particle_group = ParticleGroup(self.img_cache)

        self.component_manager = Ecs.ComponentManager()
        self.entity_manager = Ecs.EntityManager(self.component_manager)
        self.system_manager = Ecs.SystemManager(self.entity_manager, self.component_manager)

        self.p = self.entity_manager.add_entity()
        p_anim = Animation("assets/entities/player/config.json")
        self.component_manager.add_component(self.p, [
            Transform(200, 30, 5, 15),
            Image(make_surface((5, 16), color=(255, 255, 125))),
            Velocity(250, 250),
            p_anim
        ])
        self.renderer_sys = AnimationRenderer(screen)
        self.system_manager.add_system(self.p, self.renderer_sys)
        self.collision_resolver_sys = CollisionResolver()
        self.system_manager.add_system(self.p, self.collision_resolver_sys)
        self.animation_updater_sys = AnimationUpdater()
        self.system_manager.add_system(self.p, self.animation_updater_sys)

        # region Slider setup
        self.gravity_slider = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(210, 500, 500, 30),
                                                                     start_value=self.gravity,
                                                                     value_range=(1, 100),
                                                                     manager=self.pygame_gui_manager)
        self.gravity_textbox = pygame_gui.elements.ui_text_entry_box.UITextEntryBox(pygame.Rect(110, 500, 90, 30),
                                                                                    f"{self.gravity}",
                                                                                    manager=self.pygame_gui_manager)
        self.gravity_lbl = pygame_gui.elements.ui_label.UILabel(pygame.Rect(10, 500, 90, 30),
                                                                "Gravity",
                                                                self.pygame_gui_manager)
        self.max_gravity_slider = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(210, 530, 500, 30),
                                                                         start_value=self.max_gravity,
                                                                         value_range=(1, 1500),
                                                                         manager=self.pygame_gui_manager)
        self.max_gravity_lbl = pygame_gui.elements.ui_label.UILabel(pygame.Rect(10, 530, 90, 30),
                                                                    "Max. Gravity",
                                                                    self.pygame_gui_manager)
        self.max_gravity_textbox = pygame_gui.elements.ui_text_entry_box.UITextEntryBox(pygame.Rect(110, 530, 90, 30),
                                                                                        f"{self.max_gravity}",
                                                                                        manager=self.pygame_gui_manager)
        self.jumpforce_slider = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(210, 560, 500, 30),
                                                                       start_value=self.jumpforce,
                                                                       value_range=(1, 2500),
                                                                       manager=self.pygame_gui_manager)
        self.jumpforce_textbox = pygame_gui.elements.ui_text_entry_box.UITextEntryBox(pygame.Rect(110, 560, 90, 30),
                                                                                      f"{self.jumpforce}",
                                                                                      manager=self.pygame_gui_manager)
        self.jumpforce_lbl = pygame_gui.elements.ui_label.UILabel(pygame.Rect(10, 560, 90, 30),
                                                                  "Jumpforce",
                                                                  self.pygame_gui_manager)
        # endregion

        self.player_movement = [0, 0]
        self.fps_options = [0, 15, 30, 60, 120, 240]
        self.fps_idx = 0

        self.assets = {
            'decor': load_images('assets/tiles/decor'),
            'grass': load_images('assets/tiles/grass'),
            'large_decor': load_images('assets/tiles/large_decor'),
            'stone': load_images('assets/tiles/stone'),
            "bridge": load_images("assets/tiles/bridge"),
        }

        self.scroll = Vector2(0)

    def run(self):
        right = False
        left = False
        up = False
        down = False
        jump = False
        boost = False
        run__ = True

        p_velocity: Velocity = self.component_manager.get_component(self.p, Velocity)
        p_transform: Transform = self.component_manager.get_component(self.p, Transform)
        p_anim: Animation = self.component_manager.get_component(self.p, Animation)

        while run__:
            jump = False
            dt = mainClock.tick(self.fps_options[self.fps_idx]) * 0.001 * self.dt_multiplicator

            # self.scroll += ((self.player.pos - Vector2(4, 4)) - RES / 4 / 2 - self.scroll) / 30
            # scroll += ((self.p.pos - Vector2(TILESIZE / 2)) - DOWNSCALED_RES / 2 - scroll) / 30
            self.scroll += ((self.component_manager.get_component(self.p, Transform).pos - Vector2(TILESIZE / 2)) - DOWNSCALED_RES / 2 - self.scroll) / 30
            screen.fill((0, 0, 0))

            self.timermanager.update()

            if right:
                self.player_movement[0] = 1
            elif left:
                self.player_movement[0] = -1
            else:
                self.player_movement[0] = 0
            if self.noclip:
                if up:
                    self.player_movement[1] = -1
                elif down:
                    self.player_movement[1] = 1
                else:
                    self.player_movement[1] = 0

            if boost:
                self.player_movement[0] *= 4
                self.player_movement[1] *= 4

            self.tile_map.render(screen, offset=self.scroll)
            system_args = {
                "scroll": self.scroll,
                "movement": self.player_movement,
                "dt": dt,
                "tilemap": self.tile_map,
                "noclip": self.noclip,
                "gravity": self.gravity,
                "max_gravity": self.max_gravity,
                "debug_animation": "red",
                "debug_tiles": "yellow",
            }
            self.system_manager.run_all_systems(**system_args)

            # region Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    run__ = False
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
                        jump = True
                        p_velocity = self.component_manager.get_component(self.p, Velocity)
                        p_velocity.y = -self.jumpforce
                        print(p_velocity.xy)
                        # self.p.set_state("jump_init")
                    if event.key == pygame.K_TAB:
                        self.noclip = not self.noclip
                        p_velocity = self.component_manager.get_component(self.p, Velocity)
                        p_velocity.y = 0
                    if event.key == pygame.K_UP:
                        self.dt_multiplicator = min(5, self.dt_multiplicator + 0.25)
                    if event.key == pygame.K_DOWN:
                        self.dt_multiplicator = max(0, self.dt_multiplicator - 0.25)
                    if event.key == pygame.K_r:
                        p_transform = self.component_manager.get_component(self.p, Transform)
                        p_transform.pos = Vector2(200, 50)
                        p_velocity = self.component_manager.get_component(self.p, Velocity)
                        p_velocity.y = 0
                        self.particle_group.clear()
                    if event.key == pygame.K_LCTRL:
                        boost = True
                    if event.key == pygame.K_g:
                        self.fps_idx = (self.fps_idx + 1) % len(self.fps_options)
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
                    if event.ui_element == self.gravity_slider:
                        print('current slider value:', event.value)
                        self.gravity_textbox.set_text(str(event.value))
                        self.gravity = event.value
                    elif event.ui_element == self.max_gravity_slider:
                        print('current slider value:', event.value)
                        self.max_gravity_textbox.set_text(str(event.value))
                        self.max_gravity = event.value
                    elif event.ui_element == self.jumpforce_slider:
                        print('current slider value:', event.value)
                        self.jumpforce_textbox.set_text(str(event.value))
                        self.jumpforce = event.value

                if event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
                    if event.ui_element == self.gravity_textbox:
                        print("Changed text:", event.text)
                        val = self.gravity_slider.get_current_value()
                        try:
                            val = max(self.gravity_slider.value_range[0], min(int(event.text), self.gravity_slider.value_range[1]))
                            self.gravity_slider.set_current_value(val)
                            self.gravity = val
                        except ValueError:
                            print(f"Converting error: {event.text=}")
                    elif event.ui_element == self.max_gravity_textbox:
                        print("Changed text:", event.text)
                        val = self.max_gravity_slider.get_current_value()
                        try:
                            val = max(self.max_gravity_slider.value_range[0], min(int(event.text), self.max_gravity_slider.value_range[0]))
                            self.max_gravity_slider.set_current_value(val)
                            self.max_gravity = val
                        except ValueError:
                            print(f"Converting error: {event.text=}")
                    elif event.ui_element == self.jumpforce_textbox:
                        print("Changed text:", event.text)
                        val = self.jumpforce_slider.get_current_value()
                        try:
                            val = max(self.jumpforce_slider.value_range[0], min(int(event.text), self.jumpforce_slider.value_range[0]))
                            self.jumpforce_slider.set_current_value(val)
                            self.jumpforce = val
                        except ValueError:
                            print(f"Converting error: {event.text=}")
                # endregion

                self.pygame_gui_manager.process_events(event)
            # endregion

            if right or left:
                p_anim.state = "run"
            elif jump:
                p_anim.state = "jump"
            else:
                p_anim.state = "idle"
            # if self.noclip:
            #     p_anim.state = "idle"

            m_pos = tuple(pygame.Vector2(pygame.mouse.get_pos()))
            if pygame.mouse.get_pressed()[0]:
                self.particle_group.add([CircleParticle(m_pos, (random.randrange(-100, 100), random.randrange(-100, 100)), 4, type="particle") for _ in range(5)])
            if pygame.mouse.get_pressed()[2]:
                self.particle_group.add([LeafParticle(m_pos, (random.randrange(-30, 30), random.randrange(-30, 30)), 18, type="leaf") for _ in range(5)])

            self.particle_group.update(dt)
            self.particle_group.draw(screen, blend=pygame.BLEND_RGB_ADD)

            self.pygame_gui_manager.update(dt)

            master_screen.blit(pygame.transform.scale(screen, RES), (0, 0))

            outline_color = None
            p_transform = self.component_manager.get_component(self.p, Transform)
            draw_text(master_screen, f"DT: {dt:.6f} DT multiplier:{self.dt_multiplicator:.4f}", (0, 80), outline_color=outline_color)
            draw_text(master_screen, f"{mainClock.get_fps():.0f}", (500, 0), outline_color=outline_color)
            draw_text(master_screen, f"{self.player_movement[0]:.2f}, {self.player_movement[1]:.2f}", (0, 200), outline_color=outline_color)
            draw_text(master_screen, f"TILEPOS: {p_transform.pos // TILESIZE}\nPOS:{p_transform.pos}\nNOCLIP: {self.noclip}", (500, 50), outline_color=outline_color)
            draw_text(master_screen, f"PARTICLES:\nAmount of Particles: {len(self.particle_group)}", (500, 250), outline_color=outline_color)
            draw_text(master_screen, f"Anim state: {p_anim.state}", (0, 0,),  outline_color=outline_color)

            self.pygame_gui_manager.draw_ui(master_screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
