from Scripts.CONFIG import *
from Scripts.Ecs.components import BaseComponent
from Scripts.Ecs.entity import Entity
from Scripts.sprites import Animation, cut_spritesheet_row, cut_from_spritesheet
from Scripts.timer import Timer
from typing import List, Type, Tuple
from Scripts.tilemap import TileMap, FALLTRHOGH_TILES
from Scripts.utils import load_images
from . import Ecs
import json
import time
import collections
from Scripts.Ui import easings
from Scripts.utils_math import sign, dist, clamp
import random


class FrozenDict(collections.abc.Mapping):  # https://stackoverflow.com/questions/2703599/what-would-a-frozen-dict-be
    """Don't forget the docstrings!!"""

    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)
        self._hash = None

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __getitem__(self, key):
        return self._d[key]

    def __hash__(self):
        # It would have been simpler and maybe more obvious to
        # use hash(tuple(sorted(self._d.iteritems()))) from this discussion
        # so far, but this solution is O(n). I don't know what kind of
        # n we are going to run into, but sometimes it's hard to resist the
        # urge to optimize when it will gain improved algorithmic performance.
        if self._hash is None:
            hash_ = 0
            for pair in self.items():
                if isinstance(pair[1], list):
                    hash_ ^= hash((pair[0], tuple(pair[1])))
                else:
                    hash_ ^= hash(pair)
            self._hash = hash_
        return self._hash


class Transform(Ecs.BaseComponent):
    def __init__(self, x: int | float, y: int | float, w: int | float, h: int | float) -> None:
        super().__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.falling_through = False
        self.fall_through_timer = Timer(0.18, False, False)

    @property
    def xy(self) -> Tuple[int | float, int | float]:
        return (self.x, self.y)

    @property
    def rect(self) -> Rect:
        return Rect(self.x, self.y, self.w, self.h)

    @rect.setter
    def rect(self, rect: Rect) -> None:
        # print(f"rect setter ran with: {rect}")
        self.x = rect.x
        self.y = rect.y
        self.w = rect.w
        self.h = rect.h

    @property
    def frect(self) -> FRect:
        return FRect(self.x, self.y, self.w, self.h)

    @frect.setter
    def frect(self, frect: FRect) -> None:
        # print(f"frect setter ran with: {frect}")
        self.x = frect.x
        self.y = frect.y
        self.w = frect.w
        self.h = frect.h

    @property
    def pos(self) -> Vector2:
        return Vector2(self.x, self.y)

    @pos.setter
    def pos(self, pos: Vector2 | Tuple) -> None:
        self.x = pos[0]
        self.y = pos[1]

    @property
    def size(self) -> Tuple[int | float, int | float]:
        return self.w, self.h

    @size.setter
    def size(self, pos: Tuple) -> None:
        self.w = pos[0]
        self.h = pos[1]


class Velocity(Ecs.BaseComponent, Vector2):
    def __init__(self, x: int | float, y: int | float) -> None:
        Vector2.__init__(self, x, y)
        Ecs.BaseComponent.__init__(self)


class Animation(Ecs.BaseComponent):
    def __init__(self, config_file_path: str) -> None:
        super().__init__()
        self.states: dict[str, list[Surface]] = {}
        self.states_looping: dict[str, bool] = {}
        self.states_frame_times: dict[str, bool] = {}
        self.states_offset: dict[str, Tuple] = {}

        self.__state: str = None
        self.index: float = 0.0
        self._last_img: Surface = None
        self.offset = [0, 0]

        self.flip = False
        self.last_index_update: float = .0

        self.__parse_config(config_file_path)

    def __parse_config(self, path: str) -> None:
        with open(path, "r") as f:
            data = json.load(f)

            colorkey = data["colorkey"]
            default_path = data["file_path"]
            for state, state_data in data["animations"].items():
                self.states[state] = load_images(f"{default_path}/{state}", colorkey=colorkey)
                self.states_looping[state] = state_data["loop"]
                self.states_frame_times[state] = state_data["frames"]
                self.states_offset[state] = state_data["offset"]

            self.state = data["default"]
            self.offset = data["offset"]

    @property
    def state(self) -> str:
        return self.__state

    @state.setter
    def state(self, state: str) -> None:
        if state != self.__state:
            self.__state = state
            self.index = 0

    @property
    def over(self) -> bool:
        if self.states_looping[self.__state]:  # looping
            return False
        return self.index == len(self.states[self.__state]) - 1

    def add_state(self, state: str, surfs: list[Surface], looping: bool, frame_times: List[float]) -> None:
        if state not in self.states:
            self.states[state] = surfs
            self.states_looping[state] = looping
            self.states_frame_times[state] = frame_times

    def img(self) -> Surface:
        return pygame.transform.flip(self.states[self.__state][int(self.index)], self.flip, False)

    def new_img(self) -> bool:
        return self.__last_img != self.img()

    def get_offset(self) -> Tuple:
        state_offset = self.states_offset[self.state]
        return (self.offset[0] + state_offset[0], self.offset[1] + state_offset[1])


class AnimationUpdater(Ecs.BaseSystem):
    def __init__(self) -> None:
        super().__init__([Animation])

    def update_entity(self, entity: Ecs.Entity, entity_components: dict[type[Ecs.BaseComponent], Ecs.BaseComponent], **kwargs) -> None:
        anim: Animation = entity_components[Animation]
        dt = kwargs["dt"]
        movement = kwargs["movement"]

        if entity == kwargs["player_entity"]:
            if movement[0] > 0:
                anim.flip = False
            if movement[0] < 0:
                anim.flip = True

        anim._last_img = anim.img()
        curr = time.time()
        frame_time = anim.states_frame_times[anim.state][anim.index]
        if anim.states_looping[anim.state]:  # looping
            # anim.index = (anim.index + frame_time * dt) % len(anim.states[anim.state])
            if curr - anim.last_index_update > frame_time:
                anim.index = (anim.index + 1) % len(anim.states[anim.state])
                anim.last_index_update = curr
        else:  # nicht looping
            # anim.index = min(anim.index + frame_time * dt, len(anim.states[anim.state]) - 1)
            if curr - anim.last_index_update > frame_time:
                anim.index = min(anim.index + 1, len(anim.states[anim.state]) - 1)
                anim.last_index_update = curr


class Image(Ecs.BaseComponent):
    def __init__(self, image: Surface) -> None:
        super().__init__()
        self.img = image


class AnimationRenderer(Ecs.BaseSystem):
    def __init__(self, surface: Surface) -> None:
        super().__init__([Transform, Animation])
        self.surface = surface

    def update_entity(self, entity: Ecs.Entity, entity_components: dict[type[Ecs.BaseComponent], Ecs.BaseComponent], **kwargs) -> None:
        transform: Transform = entity_components[Transform]
        anim: Animation = entity_components[Animation]
        scroll = kwargs["scroll"]

        animation_offset = anim.get_offset()
        self.surface.blit(anim.img(), (transform.x - scroll[0] - animation_offset[0], transform.y - scroll[1] - animation_offset[1]))

        if "debug_animation" in kwargs:
            pygame.draw.rect(self.surface, kwargs["debug_animation"], Rect(transform.x - scroll[0], transform.y - scroll[1], transform.w, transform.h), 1)


class ImageRenderer(Ecs.BaseSystem):
    def __init__(self, surface: Surface) -> None:
        super().__init__([Transform, Image])
        self.surface = surface

    def update_entity(self, entity: Ecs.Entity, entity_components: dict[type[Ecs.BaseComponent], Ecs.BaseComponent], **kwargs) -> None:
        transform: Transform = entity_components[Transform]
        image: Image = entity_components[Image]
        scroll = kwargs["scroll"]

        self.surface.blit(image.img, (transform.x - scroll[0], transform.y - scroll[1]))


class CollisionResolver(Ecs.BaseSystem):
    def __init__(self) -> None:
        super().__init__([Transform, Velocity])
        self.last_movement = []

    def update_entity(self, entity: Ecs.Entity, entity_components: dict[type[Ecs.BaseComponent], Ecs.BaseComponent], **kwargs) -> None:
        transform: Transform = entity_components[Transform]
        velocity: Velocity = entity_components[Velocity]

        tilemap: TileMap = kwargs["tilemap"]
        movement = kwargs["movement"]
        dt = kwargs["dt"]
        noclip = kwargs["noclip"]
        max_gravity = kwargs["max_gravity"]
        gravity = kwargs["gravity"]

        return_data = {"coll_tiles": [], "collisions": None}
        collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        ignore_falltrough = kwargs["drop_through"]
        if ignore_falltrough:
            transform.falling_through = True

        if noclip:
            frame_movement = (movement[0] * 200 * dt, movement[1] * 200 * dt)
            transform.x += frame_movement[0]
            transform.y += frame_movement[1]
            return_data["collisions"] = collisions
            return return_data
        frame_movement = (movement[0] * velocity[0] * dt, 1 * velocity[1] * dt)

        collided_with_fall_trough = False
        transform.x += frame_movement[0]
        entity_rect = transform.frect
        for rect, tile in zip(tilemap.physics_rects_around(transform.pos), tilemap.get_around(transform.pos, ignore={"decor"})):
            if entity_rect.colliderect(rect):
                return_data["coll_tiles"].append(tile)
                if tile["type"] in FALLTRHOGH_TILES:  # wenn spieler nicht mehr mit fallthrough collided, dann kann man aus machen.
                    collided_with_fall_trough = True
                if frame_movement[0] > 0:  # right
                    if tile["type"] in FALLTRHOGH_TILES:
                        # transform.falling_through = True
                        pass
                    else:
                        entity_rect.right = rect.left
                        collisions['right'] = True
                if frame_movement[0] < 0:  # left
                    if tile["type"] in FALLTRHOGH_TILES:
                        # transform.falling_through = True
                        pass
                    else:
                        entity_rect.left = rect.right
                        collisions['left'] = True
                transform.x = entity_rect.x

        transform.y += frame_movement[1]
        entity_rect = transform.frect
        for rect, tile in zip(tilemap.physics_rects_around(transform.pos), tilemap.get_around(transform.pos, ignore={"decor"})):
            if entity_rect.colliderect(rect):
                return_data["coll_tiles"].append(tile)
                if tile["type"] in FALLTRHOGH_TILES:  # wenn spieler nicht mehr mit fallthrough collided, dann kann man aus machen.
                    collided_with_fall_trough = True
                if frame_movement[1] > 0:  # downards
                    if tile["type"] in FALLTRHOGH_TILES and transform.falling_through or (tile["type"] in FALLTRHOGH_TILES and (rect.y - rect.h / 2) - transform.pos.y < 1):  # durch droppen mit key input
                        pass
                    else:
                        entity_rect.bottom = rect.top
                        collisions['down'] = True
                if frame_movement[1] < 0:  # upwards
                    if tile["type"] in FALLTRHOGH_TILES:
                        pass
                    else:
                        entity_rect.top = rect.bottom
                        collisions['up'] = True
                transform.y = entity_rect.y

        # resetting fallthrough
        if not collided_with_fall_trough:
            transform.falling_through = False

        self.last_movement = movement

        velocity[1] = min(max_gravity, velocity[1] + gravity)

        if collisions['down'] or collisions['up']:
            velocity[1] = 0

        if "debug_tiles" in kwargs:
            scroll = kwargs["scroll"]
            for r in tilemap.physics_rects_around(transform.pos):
                pygame.draw.rect(screen, kwargs["debug_tiles"], Rect(r.x - scroll[0], r.y - scroll[1], r.w, r.h), 1)

        return_data["collisions"] = collisions
        return return_data


class CardData(Ecs.BaseComponent):
    def __init__(self, game, type) -> None:
        super().__init__()

        self.game = game
        self.type = type
        self.data: dict[str, object] = {}
        self.image = self.game.assets["cards"][self.type]


class CardManager(Ecs.ExtendedSystem):
    def __init__(self, game) -> None:
        super().__init__([Transform, CardData])
        self.game = game

        self.cards: List[Ecs.Entity] = []
        self.last_selected_card = 0
        self.selected_card = 0
        self.animations: dict[int, dict] = {}
        self.static: dict[int, int] = {}

    def __len__(self) -> int: return len(self.cards)

    def scroll(self, y):
        self.last_selected_card = self.selected_card
        self.selected_card = (self.selected_card + y) % len(self.cards)
        self.animate_card(self.last_selected_card, "down", 0.3)
        self.animate_card(self.selected_card, "up", 0.3)

    def add_card(self, c):
        self.cards.append(c)
        i = len(self.cards) - 1
        self.animate_card(i, "down", 0.3)
        if len(self.cards) == 1:
            self.scroll(1)

    def remove_card(self):
        if not self.cards:
            return
        e = self.cards.pop(0)
        if 0 in self.animations:
            del self.animations[0]
        if 0 in self.static:
            del self.static[0]

        a = self.selected_card
        self.selected_card = clamp(0, self.selected_card-1, len(self.cards)-1)
        if a == 0 and self.selected_card == 0 and self.cards:
            self.animate_card(0, "up", 0.3)

        l = []
        for id in self.animations:
            if id:
                l.append(id)
        self.animations = {(i-1 if i in l else i): d for i, d in self.animations.items()}
        l.clear()
        for id in self.static:
            if id:
                l.append(id)
        self.static = {(i-1 if i in l else i): d for i, d in self.static.items()}
        return e

    def animate_card(self, id, direction, duration):
        dir = 20 if direction == "down" else -20
        self.animations[id] = {"direction": dir,
                               "duration": duration,
                               "start_time": time.time(),
                               "time": time.time()}
        if id in self.static:
            del self.static[id]

    def animate(self, id, dt) -> int:
        if id not in self.animations:
            return self.static[id]
        self.animations[id]["time"] += dt
        passed_time = min(self.animations[id]["time"] - self.animations[id]["start_time"], self.animations[id]["duration"])
        t = passed_time / self.animations[id]["duration"]
        ret = self.animations[id]["direction"] * easings.ease_linear(t)  # / data["direction"]

        if passed_time == self.animations[id]["duration"]:
            del self.animations[id]
            self.static[id] = ret

        return ret

    def update_entities(self, entites_data: dict[Entity, dict[type[BaseComponent], BaseComponent]], **kwargs) -> None:
        dt = kwargs["dt"]
        print(self.animations, self.static, entites_data)

        bar_middle_pos = (DOWNSCALED_RES.x / 2, DOWNSCALED_RES.y - 75)
        card_size = (48 * 0.8, 67)
        n_entities = len(self.cards)
        total_shift = n_entities * card_size[0] / 2
        a = -3
        b = int(n_entities / 2)
        c = bar_middle_pos[1]
        for i, (entity, entity_components) in enumerate(entites_data.items()):
            transform: Transform = entity_components[Transform]

            transform.pos = (
                bar_middle_pos[0] + card_size[0] * i - total_shift,
                -a * (i - b) ** 2 + c + self.animate(i, dt)
            )


class CardRenderer(Ecs.ExtendedSystem):
    def __init__(self, screen: Surface) -> None:
        super().__init__([CardData, Transform])
        self.screen = screen

    def update_entities(self, entites_data: dict[Entity, dict[type[BaseComponent], BaseComponent]], **kwargs) -> None:
        fblits = []
        for i, (entity, entity_components) in enumerate(entites_data.items()):
            transform: Transform = entity_components[Transform]
            card: CardData = entity_components[CardData]
            fblits.append((card.image, transform.pos))
        self.screen.fblits(fblits)


class EnemyCollisionResolver(Ecs.BaseSystem):
    def __init__(self, enemypathfinder) -> None:
        super().__init__([Transform, Velocity])
        self.enemypathfinder = enemypathfinder

    def update_entity(self, entity: Entity, entity_components: dict[type[BaseComponent], BaseComponent], **kwargs) -> None:
        transform: Transform = entity_components[Transform]
        velocity: Velocity = entity_components[Velocity]

        tilemap: TileMap = kwargs["tilemap"]
        dt = kwargs["dt"]
        max_gravity = kwargs["max_gravity"]
        gravity = kwargs["gravity"]

        return_data = {"coll_tiles": [], "collisions": None}
        collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        frame_movement = (bool(velocity.x) * velocity[0] * dt, 1 * velocity[1] * dt)

        transform.x += frame_movement[0]
        entity_rect = transform.frect
        for rect, tile in zip(tilemap.physics_rects_around(transform.pos), tilemap.get_around(transform.pos)):
            if entity_rect.colliderect(rect):
                return_data["coll_tiles"].append(tile)
                if frame_movement[0] > 0:  # right
                    if tile["type"] in FALLTRHOGH_TILES:
                        # transform.falling_through = True
                        pass
                    else:
                        entity_rect.right = rect.left
                        collisions['right'] = True
                if frame_movement[0] < 0:  # left
                    if tile["type"] in FALLTRHOGH_TILES:
                        # transform.falling_through = True
                        pass
                    else:
                        entity_rect.left = rect.right
                        collisions['left'] = True
                transform.x = entity_rect.x

        transform.y += frame_movement[1]
        entity_rect = transform.frect
        for rect, tile in zip(tilemap.physics_rects_around(transform.pos), tilemap.get_around(transform.pos)):
            if entity_rect.colliderect(rect):
                return_data["coll_tiles"].append(tile)
                if frame_movement[1] > 0:  # downards
                    if tile["type"] in FALLTRHOGH_TILES and transform.falling_through or (tile["type"] in FALLTRHOGH_TILES and (rect.y - rect.h / 2) - transform.pos.y < 1):  # durch droppen mit key input
                        pass
                    else:
                        entity_rect.bottom = rect.top
                        collisions['down'] = True
                if frame_movement[1] < 0:  # upwards
                    if tile["type"] in FALLTRHOGH_TILES:
                        pass
                    else:
                        entity_rect.top = rect.bottom
                        collisions['up'] = True
                transform.y = entity_rect.y

        velocity[1] = min(max_gravity, velocity[1] + gravity)

        if collisions['down'] or collisions['up']:
            velocity[1] = 0

        if "debug_tiles" in kwargs:
            scroll = kwargs["scroll"]
            for r in tilemap.physics_rects_around(transform.pos):
                pygame.draw.rect(screen, kwargs["debug_tiles"], Rect(r.x - scroll[0], r.y - scroll[1], r.w, r.h), 1)

        self.enemypathfinder.collisions = collisions

        return_data["collisions"] = collisions
        return return_data


def skalar(p1, p2):
    return (p1[0] * p2[0] + p1[1] * p2[1])


class Ray:
    def __init__(self, origin, direction) -> None:
        self.origin = origin
        l = sum(direction)
        self.direction = (-direction[0] / l, -direction[1] / l)  # v / ||v||

    def hit(self, pos, width=4) -> Tuple:
        # https://gdbooks.gitbooks.io/3dcollisions/content/Chapter1/closest_point_on_line.html
        a = self.origin
        b = (self.origin[0] + self.direction[0], self.origin[1] + self.direction[1])
        c = pos

        # t = Dot(c - a, ab) / Dot(ab, ab)
        # point = a + t * ab

        t = skalar(c - a, b - a) / skalar(b - a, b - a)
        point = a + t * (b - a)

        d = dist(point, pos)
        # print(a, b, c, self.direction, point, pos, t, d)
        if d >= width:
            return False
        return True


class EnemyPathFinderWalker(Ecs.BaseSystem):
    def __init__(self, target_entity) -> None:
        super().__init__([Transform, Velocity, Animation])

        self.target_entity = target_entity
        self.walking = False
        self.active = False
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        self.charge = .0
        self.charge_duration = .3
        self.target_point = None

    def update_entity(self, entity: Entity, entity_components: dict[type[BaseComponent], BaseComponent], **kwargs) -> bool:
        transform: Transform = entity_components[Transform]
        velocity: Velocity = entity_components[Velocity]
        anim: Animation = entity_components[Animation]

        dt = kwargs["dt"]
        tilemap: TileMap = kwargs["tilemap"]

        d = 100
        walking_target_pos = None
        shoot = False
        player_hit = False
        target_transform: Transform = self.component_manager.get_component(self.target_entity, Transform)

        if self.walking:
            if tilemap.solid_check((walking_target_pos := (transform.rect.centerx + (-7 if anim.flip else 7), transform.y + tilemap.tile_size))):
                if self.collisions["right"] or self.collisions["left"]:
                    anim.flip = not anim.flip
                velocity.x = -15 if anim.flip else 15
            else:
                anim.flip = not anim.flip

        if self.active:
            if not self.target_point:
                self.target_point = target_transform.rect.center
            self.charge += dt
            if self.charge >= self.charge_duration:
                shoot = True
                self.charge = 0

        if shoot:
            print("shooting")
            # direction = (self.target_point[0] - transform.x, self.target_point[1] - transform.y)
            direction = self.target_point - transform.pos
            ray = Ray(transform.pos, direction)
            for entitiy in [self.target_entity]:
                if ray.hit(target_transform.rect.center):  # (richtige pos benutzen) dmg dealen oder sonst was hier ...
                    player_hit = True
            self.target_point = None

        if dist(target_transform.rect.center, transform.pos) < d:
            self.walking = False
            self.active = True
            velocity.x = 0
            anim.state = "idle"
        else:
            self.walking = True
            self.active = False
            anim.state = "run"
            self.charge = 0
            self.target_point = None

        transform.x += velocity.x * dt
        transform.y += velocity.y * dt

        if self.active and self.target_point:
            scroll = kwargs["scroll"]
            a = transform.pos
            b = self.target_point
            t = self.charge / self.charge_duration
            t = easings.ease_in_circ(t)
            c = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            pygame.draw.line(kwargs["surface"], (0, 255, 0), (a[0] - scroll[0], a[1] - scroll[1]), (c[0] - scroll[0], c[1] - scroll[1]), 1)

        if "debug_pathfinder" in kwargs:
            scroll = kwargs["scroll"]
            if walking_target_pos:
                pygame.draw.circle(kwargs["surface"], kwargs["debug_pathfinder"], (walking_target_pos[0] - scroll[0], walking_target_pos[1] - scroll[1]), 3)
                r = Rect(((walking_target_pos[0] // 16) * 16) - scroll[0], ((walking_target_pos[1] // 16) * 16) - scroll[1], 16, 16)
                pygame.draw.rect(kwargs["surface"], kwargs["debug_pathfinder"], r, 1)

            pygame.draw.circle(kwargs["surface"], kwargs["debug_pathfinder"], (transform.x - scroll[0], transform.y - scroll[1]), d, 1)
            if self.active:
                tp = target_transform.rect.center
                pygame.draw.line(kwargs["surface"], kwargs["debug_pathfinder"], (tp[0] - scroll[0], tp[1] - scroll[1]), (transform.rect.centerx - scroll[0], transform.rect.centery - scroll[1]), 1)

                if self.target_point:
                    pygame.draw.circle(kwargs["surface"], (255, 0, 0), (self.target_point[0] - scroll[0], self.target_point[1] - scroll[1]), 3)

        return player_hit
