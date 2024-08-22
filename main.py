import sys
import pygame_gui
import pygame_gui.ui_manager
import random
import pygame
import os
import math

from Scripts.tilemap import TileMap
from Scripts.CONFIG import *
from Scripts.utils import load_image, draw_text, random_color, make_surface, load_images, pallete_swap_dir
from Scripts.particles import ParticleGroup, ImageCache, CircleParticle, LeafParticle, Spark
from Scripts.timer import TimerManager

from Scripts.entities import (Transform,
                              Velocity,
                              CollisionResolver,
                              Animation,
                              AnimationRenderer,
                              Image,
                              ImageRenderer,
                              AnimationUpdater,
                              EnemyPathFinderWalker,
                              EnemyCollisionResolver,
                              ParticleSystemRenderer,
                              ParticleSystemUpdater,
                              Item,
                              ItemRenderer,
                              Gun,
                              ItemManager,
                              Inventory,
                              ItemPhysics,
                              ProjectileData,
                              ProjectileManager,
                              RemoveAfterTime,
                              InvetoryRenderer)

import Scripts.Ecs as Ecs


os.environ['SDL_VIDEO_CENTERED'] = '1'

pygame.init()
pygame.font.init()

enemy_pos = (0, 0)

PROJECTILE_DECAY_TIME = 4  # in s


class Game:
    def __init__(self) -> None:
        # self.timermanager = TimerManager()
        self.dt_multiplicator = 1
        self.gravity = 6
        self.max_gravity = 700
        self.jumpforce = 10000  # 600
        self.noclip = False
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
            Velocity(250, 250),
            p_anim,
            Inventory()
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

        self.enemies = []
        self.items = []
        self.sparks: list[Spark] = []

        self.assets = {
            'decor': load_images('assets/tiles/decor'),
            'grass': load_images('assets/tiles/grass'),
            'large_decor': load_images('assets/tiles/large_decor'),
            'stone': load_images('assets/tiles/stone'),
            "bridge": load_images("assets/tiles/bridge"),
            "cards": {
                "dash": load_image("assets/cards/dash.png"),
                "knifes": load_image("assets/cards/knifes.png"),
                # "invisibility": load_image("assets/cards/invisibility.png"),
                # "clone": load_image("assets/cards/clone.png"),
                # "grapple": load_image("assets/cards/grapple.png"),
                # "health_swap": load_image("assets/cards/health_swap.png"),
                # "health": load_image("assets/cards/health.png"),
                # "shield": load_image("assets/cards/shield.png"),
                # "lightning": load_image("assets/cards/lightning.png"),
                # "timeshift": load_image("assets/cards/timeshift.png"),
                # "boomerang": load_image("assets/cards/boomerang.png"),
            },
            "grass_blades_cover": [load_image("assets/tiles/blades_cover.png")],
            "grass_blades": load_images("assets/tiles/grass_blades"),
            "particles": {
                "particle": pallete_swap_dir(load_images("assets/particles/particle"), [(255, 255, 255)], [(255, 0, 0)]),
                "leaf": pallete_swap_dir(load_images("assets/particles/leaf"), [(255, 255, 255)], [(0, 255, 0)]),
            },
            "items": {
                "apple": load_image("assets/items/apple.png"),
                "guns/rifle": load_image("assets/items/guns/rifle.png"),
                "guns/pistol": load_image("assets/items/guns/pistol.png"),
                "guns/shotgun": load_image("assets/items/guns/shotgun.png"),
                "guns/rocketlauncher": load_image("assets/items/guns/rocketlauncher.png"),
                "guns/projectile": load_image("assets/items/guns/projectile.png"),
            },
        }

        self.scroll = Vector2(0)

        self.tile_map.init_grass()

        self.particle_renderer = ParticleSystemRenderer(screen)
        self.particle_updater = ParticleSystemUpdater()
        self.enemy_path_finder_walker = EnemyPathFinderWalker(self.p)
        self.enemy_coll_resolver = EnemyCollisionResolver(self.enemy_path_finder_walker)
        self.item_physics = ItemPhysics()
        self.item_manager = ItemManager()
        self.item_renderer = ItemRenderer(self, screen)
        self.inventory_renderer = InvetoryRenderer(self, screen)
        self.system_manager.add_system(self.p, self.inventory_renderer)

        self.system_manager.add_system(self.p, self.item_manager)

        self.parsemap()

    def parsemap(self):
        for spawner in self.tile_map.extract([('spawners', 0), ('spawners', 1), ("spawners", 2), ("spawners", 3), ("spawners", 4), ("spawners", 5), ("spawners", 6)], keep=False):
            # print(spawner)
            if spawner["variant"] == 0:
                self.component_manager.get_component(self.p, Transform).pos = spawner["pos"]
            if spawner["variant"] == 1:
                enemy = self.entity_manager.add_entity()
                self.component_manager.add_component(enemy, [
                    Transform(*spawner["pos"], 7, 11),
                    Animation("assets/entities/enemies/walker/config.json"),
                    Velocity(15, 0),
                ])
                self.system_manager.add_system(enemy, self.animation_updater_sys)
                self.system_manager.add_system(enemy, self.renderer_sys)
                self.system_manager.add_system(enemy, self.enemy_path_finder_walker)
                self.system_manager.add_system(enemy, self.enemy_coll_resolver)
                self.enemies.append(enemy)
            if spawner["variant"] in [2, 3, 4, 5, 6]:
                lt = {2: "guns/rifle", 3: "guns/pistol", 4: "guns/shotgun", 5: "guns/rocketlauncher", 6: "apple"}
                ltn = {2: "rifle", 3: "pistol", 4: "shotgun", 5: "rocketlauncher", 6: "godapple"}
                i = self.entity_manager.add_entity()
                item_comp = Item(self, lt[spawner["variant"]], "apple") if spawner["variant"] == 6 else Gun(self, lt[spawner["variant"]], lt[spawner["variant"]])
                self.component_manager.add_component(i, [Transform(*spawner["pos"], 4, 6),
                                                         item_comp,
                                                         Velocity(-20, -200)])
                self.system_manager.add_extended_system(i, self.item_renderer)
                self.system_manager.add_extended_system(i, self.item_physics)
                self.items.append(i)

    def add_particle(self, type: str, rect, vel):
        p = self.entity_manager.add_entity()
        self.component_manager.add_component(p, [Animation(f"assets/particles/{type}/config.json", loaded_already=self.assets["particles"][type]),
                                                 Velocity(*vel),
                                                 Transform(rect.x, rect.y, rect.w, rect.h)])
        self.system_manager.add_extended_system(p, self.particle_updater)
        self.system_manager.add_extended_system(p, self.particle_renderer)
        self.system_manager.add_system(p, self.animation_updater_sys)

    def run(self):
        right = False
        left = False
        up = False
        down = False
        jump = False
        reached_max_jump = False
        boost = False
        drop_trough = False
        run__ = True
        pickup = False
        drop = False

        p_velocity: Velocity = self.component_manager.get_component(self.p, Velocity)
        p_transform: Transform = self.component_manager.get_component(self.p, Transform)
        p_anim: Animation = self.component_manager.get_component(self.p, Animation)

        projectile_manager = ProjectileManager()
        image_renderer = ImageRenderer(screen)

        master_time = 0

        projectiles = []

        while run__:
            jump = False
            dt = mainClock.tick(self.fps_options[self.fps_idx]) * 0.001 * self.dt_multiplicator
            master_time += dt * 100
            TimerManager.update()
            # self.scroll += ((self.player.pos - Vector2(4, 4)) - RES / 4 / 2 - self.scroll) / 30
            # scroll += ((self.p.pos - Vector2(TILESIZE / 2)) - DOWNSCALED_RES / 2 - scroll) / 30
            self.scroll += ((self.component_manager.get_component(self.p, Transform).pos - Vector2(TILESIZE / 2)) - DOWNSCALED_RES / 2 - self.scroll) / 30
            screen.fill((0, 0, 0))

            def rot_function(x) -> int: return int(math.sin(master_time / 60 + x / 100) * 15)
            # def rot_function(x): return 1
            self.tile_map.rotate_grass(rot_function=rot_function)
            all_entity_rects = [p_transform.frect] + [self.component_manager.get_component(en, Transform).frect for en in self.enemies + self.items]
            self.tile_map.update_grass(all_entity_rects, 1, 12, particle_method=self.add_particle)

            if right:
                self.player_movement[0] = 1
                p_velocity.x = 200
            elif left:
                p_velocity.x = -200
                self.player_movement[0] = 1
            else:
                self.player_movement[0] = 0
                p_velocity.x = 0
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
                "movement_anim": [-1 if left else (1 if right else 0), -1 if up else (1 if down else 0)],
                "dt": dt,
                "tilemap": self.tile_map,
                "noclip": self.noclip,
                "gravity": self.gravity,
                "max_gravity": self.max_gravity,
                "player_entity": self.p,
                "drop_through": drop_trough,
                # "debug_animation": (255,0,0),
                "debug_tiles": (255, 255, 0),
                # "debug_pathfinder": (255, 0, 255),
                # "debug_items": (0, 255, 255),
                # "debug_projectiles": (255, 0, 255),
                "surface": screen,  # eig. nicht gut das so zu machen oder etwa doch ??
                "all_items": self.items,
                "pickup": pickup,
                "drop": drop,
            }
            systems_ret = self.system_manager.run_all_systems(**system_args)
            if systems_ret[CollisionResolver][self.collision_resolver_sys][self.p]["collisions"]["down"]:
                reached_max_jump = False
            if systems_ret[ParticleSystemUpdater]:
                for e in systems_ret[ParticleSystemUpdater][self.particle_updater]:
                    self.entity_manager.remove_entity(e)

            for _, manager in systems_ret[ItemManager].items():
                for attached_entity, data in manager.items():
                    for ens, stats in data.items():
                        proj = self.entity_manager.add_entity()
                        r = stats["rect"]
                        self.component_manager.add_component(proj, [Transform(r.x, r.y, r.w, r.h),
                                                                    Velocity(*stats["vel"]),
                                                                    ProjectileData(stats["dmg"], ens[1]),
                                                                    Image(self.assets["items"]["guns/projectile"], angle=stats["angle"]),
                                                                    RemoveAfterTime(PROJECTILE_DECAY_TIME)])
                        self.system_manager.add_system(proj, projectile_manager)
                        self.system_manager.add_system(proj, image_renderer)
                        projectiles.append(proj)

                        # sparks
                        for i in range(4):
                            self.sparks.append(
                                Spark(
                                    (r.x, r.y),
                                    random.random() - 0.5 + (math.pi if stats["vel"][1] > 0 else 0),
                                    3 + random.random()
                                )
                            )
            for proj in projectiles.copy():
                transform = self.component_manager.get_component(proj, Transform)
                removeaftertime = self.component_manager.get_component(proj, RemoveAfterTime)
                if self.tile_map.solid_check(transform.pos):
                    velocity = self.component_manager.get_component(proj, Velocity)
                    projectiles.remove(proj)
                    self.entity_manager.remove_entity(proj)
                    for i in range(4):
                        self.sparks.append(
                            Spark(
                                (transform.x, transform.y),
                                random.random() - 0.5 + (math.pi if velocity.y > 0 else 0),
                                3 + random.random()
                            )
                        )
                else:
                    if removeaftertime.timer.ended:
                        projectiles.remove(proj)
                        self.entity_manager.remove_entity(proj)

            # region Events
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE] and not reached_max_jump:
                jump = True
                # p_velocity.y -= (self.jumpforce / (1+p_velocity.y))  # * dt
                p_velocity.y -= self.jumpforce / (400 - p_velocity.y)
                # 1 - 1/x
                # p_velocity.y -= self.jumpforce * dt
                # p_velocity.y -= (14 - 1 / (p_velocity.y + 10))
                if p_velocity.y <= -400:
                    reached_max_jump = True

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
                    if event.key == pygame.K_e:
                        pickup = True
                    if event.key == pygame.K_q:
                        drop = True
                    if event.key == pygame.K_TAB:
                        self.noclip = not self.noclip
                        p_velocity.y = 0
                    if event.key == pygame.K_UP:
                        self.dt_multiplicator = min(5, self.dt_multiplicator + 0.25)
                    if event.key == pygame.K_DOWN:
                        self.dt_multiplicator = max(0, self.dt_multiplicator - 0.25)
                    if event.key == pygame.K_z:
                        p_transform.pos = Vector2(200, 50)
                        p_velocity.y = 0
                        self.particle_group.clear()
                    if event.key == pygame.K_LSHIFT:
                        drop_trough = True
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
                    if event.key == pygame.K_e:
                        pickup = False
                    if event.key == pygame.K_q:
                        drop = False
                    if event.key == pygame.K_LCTRL:
                        boost = False
                    if event.key == pygame.K_LSHIFT:
                        drop_trough = False
                    if event.key == pygame.K_SPACE:
                        reached_max_jump = True

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

            for spark in self.sparks.copy():
                spark.render(screen, self.scroll)
                if spark.update(dt):
                    self.sparks.remove(spark)

            self.pygame_gui_manager.update(dt)

            master_screen.blit(pygame.transform.scale(screen, RES), (0, 0))

            outline_color = None
            draw_text(master_screen, f"DT: {dt:.6f} DT multiplier:{self.dt_multiplicator:.4f}", (0, 80), outline_color=outline_color)
            draw_text(master_screen, f"{mainClock.get_fps():.0f}", (500, 0), outline_color=outline_color)
            draw_text(master_screen, f"{self.player_movement[0]:.2f}, {self.player_movement[1]:.2f}, {p_velocity.xy}", (0, 200), outline_color=outline_color)
            draw_text(master_screen, f"TILEPOS: {p_transform.tile_pos()}\nPOS:{p_transform.pos}\nNOCLIP: {self.noclip}", (500, 50), outline_color=outline_color)
            draw_text(master_screen, f"PARTICLES:\nAmount of Particles: {len(self.particle_group)}", (500, 250), outline_color=outline_color)
            draw_text(master_screen, f"Anim state: {p_anim.state}", (0, 0,), outline_color=outline_color)

            # self.pygame_gui_manager.draw_ui(master_screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
