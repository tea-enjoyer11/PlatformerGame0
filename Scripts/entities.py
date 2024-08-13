from Scripts.CONFIG import *
from Scripts.Ecs.components import BaseComponent
from Scripts.Ecs.entity import Entity
from Scripts.tiles import *
from Scripts.sprites import Animation, cut_spritesheet_row, cut_from_spritesheet
from Scripts.timer import Timer
from typing import List, Type

# from Ecs.components import BaseComponent, BaseSystem
# from Ecs.entity import Entity
# from Ecs.managers import EntityManager, ComponentManager, SystemManager
from . import Ecs


class Transform(Ecs.BaseComponent):
    def __init__(self, x: int | float, y: int | float, w: int | float, h: int | float) -> None:
        super().__init__()
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    @property
    def xy(self) -> Tuple[int | float, int | float]:
        return (self.x, self.y)

    @property
    def rect(self) -> Rect:
        return Rect(self.x, self.y, self.w, self.h)

    @rect.setter
    def rect(self, rect: Rect) -> None:
        print(f"rect setter ran with: {rect}")
        self.x = rect.x
        self.y = rect.y
        self.w = rect.w
        self.h = rect.h

    @property
    def frect(self) -> FRect:
        return FRect(self.x, self.y, self.w, self.h)

    @frect.setter
    def frect(self, frect: FRect) -> None:
        print(f"frect setter ran with: {frect}")
        self.x = frect.x
        self.y = frect.y
        self.w = frect.w
        self.h = frect.h

    @property
    def pos(self) -> Vector2:
        return Vector2(self.x, self.y)

    @property
    def size(self) -> Tuple[int | float, int | float]:
        return self.w, self.h


class Velocity(Ecs.BaseComponent, Vector2):
    def __init__(self, x: int | float, y: int | float) -> None:
        Vector2.__init__(self, x, y)
        Ecs.BaseComponent.__init__(self)
    # def __init__(self, x: int | float, y: int | float) -> None:
    #     super().__init__()
    #     self.x = x
    #     self.y = y
    #     self.vec = pygame.Vector2(x, y)

    # def __getattr__(self, name: str) -> Any:
    #     return self.vec.__getattribute__(name)


class Animation(Ecs.BaseComponent):
    def __init__(self, images: List[Surface]) -> None:
        super().__init__()
        self.states: dict[str, list[Surface]] = {}
        self.states_looping: dict[str, bool] = {}
        self.states_frame_time: dict[str, bool] = {}

        self.__state: str = None
        self.index: float = 0.0
        self._last_img: Surface = None

    @property
    def state(self) -> str:
        return self.__state

    @state.setter
    def state(self, state: str) -> None:
        self.__state = state
        self.index = 0

    @property
    def over(self) -> bool:
        if self.states_looping[self.__state]:  # looping
            return False
        return self.index == len(self.states[self.__state]) - 1

    def add_state(self, state: str, surfs: list[Surface], looping: bool = True, frame_time: int = 4) -> None:
        if state not in self.states:
            self.states[state] = surfs
            self.states_looping[state] = looping
            self.states_frame_time[state] = frame_time

    def img(self) -> Surface:
        return self.states[self.__state][int(self.index)]

    def new_img(self) -> bool:
        return self.__last_img != self.img()


class AnimationUpdater(Ecs.BaseSystem):
    def __init__(self) -> None:
        super().__init__([Animation])

    def update_entity(self, entity: Ecs.Entity, entity_components: dict[type[Ecs.BaseComponent], Ecs.BaseComponent], **kwargs) -> None:
        anim: Animation = entity_components[Animation]
        dt = kwargs["dt"]

        anim._last_img = anim.img()
        change = anim.states_frame_time[anim.state]
        if anim.states_looping[anim.state]:  # looping
            anim.index = (anim.index + change * dt) % len(anim.states[anim.state])
        else:  # nicht looping
            anim.index = min(anim.index + change * dt, len(anim.states[anim.state]) - 1)


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

        self.surface.blit(anim.img(), transform.xy)


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

    def update_entity(self, entity: Ecs.Entity, entity_components: dict[type[Ecs.BaseComponent], Ecs.BaseComponent], **kwargs) -> None:
        # return super().update_entity(entity, entity_components, **kwargs)
        transform: Transform = entity_components[Transform]
        velocity: Velocity = entity_components[Velocity]
        tilemap: TileMap = kwargs["tilemap"]
        movement = kwargs["movement"]
        dt = kwargs["dt"]
        noclip = kwargs["noclip"]

        if noclip:
            return

        collision_types = {"left": False, "right": False, "up": False, "bottom": False}
        tiles = tilemap.get_around(transform.pos)
        normal_tiles = [tile_rect(t) for t in tiles if t.type == TileType.TILE]
        # ramps: List[Ramp] = [t for t in tiles if t.type in [TileType.RAMP_LEFT, TileType.RAMP_RIGHT]]
        # custom_ramps: List[CustomRamp] = [t for t in tiles if t.type is TileType.RAMP_CUSTOM]
        # custom_tiles: List[CustomTile] = [t for t in tiles if t.type is TileType.TILE_CUSTOM]

        tile_hit_list = collision_test(transform.frect, normal_tiles)
        # print(1, tile_hit_list)
        for t in tile_hit_list:
            r_copy = transform.frect
            if movement[1] > 0:
                r_copy.bottom = t.top
                collision_types['bottom'] = True
            elif movement[1] < 0:
                r_copy.top = t.bottom
                collision_types['top'] = True
            transform.frect = r_copy
        tile_hit_list = collision_test(transform.frect, normal_tiles)
        # print(2, tile_hit_list)
        for t in tile_hit_list:
            r_copy = transform.frect
            if movement[0] > 0:
                r_copy.right = t.left
                collision_types['right'] = True
            elif movement[0] < 0:
                r_copy.left = t.right
                collision_types['left'] = True
            transform.frect = r_copy

        if collision_types["bottom"]:
            print("vel.y reset to 0")
            velocity.y = 0


class PhysicsMovementSystem(Ecs.BaseSystem):
    def __init__(self) -> None:
        super().__init__([Transform, Velocity])

    def update_entity(self, entity: Entity, entity_components: dict[type[BaseComponent], BaseComponent], **kwargs) -> None:
        transform: Transform = entity_components[Transform]
        velocity: Velocity = entity_components[Velocity]
        movement = kwargs["movement"]
        dt = kwargs["dt"]

        transform.x += movement[0] * dt * velocity.x
        transform.y += movement[1] * dt * velocity.y


# class PhysicsEntity:
#     __slots__ = ("pos", "_last_pos", "size", "vel", "rect", "min_step_height",
#                  "_collision_types", "_last_collision_types")

#     def __init__(self, pos: Vector2, size: Vector2) -> None:
#         self.pos = pos
#         self._last_pos = Vector2(0)
#         self.size = size
#         self.vel = Vector2(0)
#         self.rect = Rect(pos.x, pos.y, size.x, size.y)
#         self.min_step_height = 0.3  # in TILESIZE Größe gerechnet

#         self._collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}
#         self._last_collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}

#     def _is_steppable(self, tile: Rect) -> bool:
#         top_point = tile.y - tile.height
#         # print(top_point - self.pos.y <= self.min_step_height * TILESIZE)
#         return top_point - self.pos.y <= self.min_step_height * TILESIZE and self._last_collision_types["bottom"] and (self._last_collision_types["right"] or self._last_collision_types["left"])

#     def _is_steppable_ramp(self, ramp: Ramp | CustomRamp) -> bool:
#         if isinstance(ramp, Ramp):
#             return TILESIZE * ramp.elevation <= self.min_step_height * TILESIZE
#         return ramp.size.y <= self.min_step_height * TILESIZE

#     def _is_steppable_custom_tile(self, c_tile: CustomTile, tile_height: float) -> bool:
#         # steppable = (TILESIZE - tile_height) < self.min_step_height * TILESIZE
#         diff = abs(self._last_pos.y - self.pos.y)
#         # print(diff, diff * TILESIZE, TILESIZE * self.min_step_height, diff <= TILESIZE * self.min_step_height)
#         return diff <= TILESIZE * self.min_step_height


# class Player(PhysicsEntity):
#     def __init__(self, pos: Vector2) -> None:
#         super().__init__(pos, Vector2(TILESIZE // 2, TILESIZE))

#         self.animation = Animation()
#         path = "assets/entities/AnimationSheet_Character.png"
#         s = Vector2(32)
#         self.animation.add_state("idle", cut_spritesheet_row(path, s, 0), frame_time=3)
#         self.animation.add_state("idle_alt", cut_spritesheet_row(path, s, 1), frame_time=3)
#         self.animation.add_state("walk", cut_spritesheet_row(path, s, 2), frame_time=6)
#         self.animation.add_state("run", cut_spritesheet_row(path, s, 3), frame_time=12)
#         self.animation.add_state("jump_init", cut_spritesheet_row(path, s, 5, max_frames=4), looping=False, frame_time=12)
#         self.animation.add_state("jump_fall", cut_spritesheet_row(path, s, 5, max_frames=2, starting_frame=5), looping=False, frame_time=12)

#         self.animation.state = "idle"

#         self.mask = from_surface(self.animation.img())  # falls ich überhaupt diese Maske haben will, sonst weg damit!

#         self.last_movement_dir = [0, 0]

#     def _handle_standart_colls(self, movement, dt: float, normal_tiles: List[Tile]) -> None:
#         self.pos[0] += movement[0] * dt
#         self.rect.x = int(self.pos[0])
#         tile_hit_list = collision_test(self.rect, normal_tiles)
#         # print(1, tile_hit_list)
#         for t in tile_hit_list:
#             if movement[0] > 0:
#                 self.rect.right = t.left
#                 self._collision_types['right'] = True
#             elif movement[0] < 0:
#                 self.rect.left = t.right
#                 self._collision_types['left'] = True
#             self.pos[0] = self.rect.x
#             # if self._is_steppable(t):  # das funktioniert nur wenn man an der linken kannte des spielers steht, dann auch nur bis dtmultiplier 2.5, ab 3.0 gehts net mehr TODO: FIXEN
#             #     self.rect.bottom = t.top
#             #     self._collision_types['bottom'] = True
#             #     self.pos[1] = self.rect.y - 1  # kleiner offset, damit der Spieler nicht an der Kante stecken bleibt
#         self.pos[1] += movement[1] * dt
#         self.rect.y = int(self.pos[1])
#         tile_hit_list = collision_test(self.rect, normal_tiles)
#         # print(2, tile_hit_list)
#         for t in tile_hit_list:
#             if movement[1] > 0:
#                 self.rect.bottom = t.top
#                 self._collision_types['bottom'] = True
#             elif movement[1] < 0:
#                 self.rect.top = t.bottom
#                 self._collision_types['top'] = True
#             self.pos[1] = self.rect.y

#     def _handle_ramps_colls(self, movement, dt: float, ramps: List[Ramp]) -> None:
#         for ramp in ramps:
#             hitbox = tile_rect(ramp)
#             ramp_collision = self.rect.colliderect(hitbox)

#             # TODO: Check einbauen, wo wenn man von der Seite auf die Ramp läuft, wo eigentlich die Wand ist, dass der Spieler da an der Kante hängen bleibt. (später min stepp offset einbauen)

#             if ramp_collision:  # check if player collided with the bounding box for the ramp
#                 # get player's position relative to the ramp on the x axis
#                 rel_x = self.rect.x - hitbox.x
#                 max_ramp_height = TILESIZE * ramp.elevation
#                 ramp_height = 0  # eine Art offset height

#                 steppable = self._is_steppable_ramp(ramp)

#                 border_collision_threshold = 5
#                 if ramp.type == TileType.RAMP_RIGHT:
#                     rel_x += self.rect.width
#                     ramp_height = rel_x * ramp.elevation

#                     # min. stepheight
#                     rel_x_border = self.rect.x - (hitbox.x + TILESIZE)  # wie nah ist der Spieler an der Kante?
#                     if movement[0] < 0 and (0 < abs(rel_x_border) <= border_collision_threshold) and not steppable:
#                         ramp_height = 0
#                         self.rect.left = hitbox.right
#                         self._collision_types['left'] = True
#                         self.pos[0] = self.rect.x
#                 elif ramp.type == TileType.RAMP_LEFT:
#                     ramp_height = (TILESIZE * ramp.elevation) - rel_x * ramp.elevation

#                     # min. stepheight
#                     rel_x_border = self.rect.x - hitbox.x + self.rect.width  # wie nah ist der Spieler an der Kante?
#                     if movement[0] > 0 and (0 < abs(rel_x_border) <= border_collision_threshold) and not steppable:
#                         ramp_height = 0
#                         self.rect.right = hitbox.left
#                         self._collision_types['right'] = True
#                         self.pos[0] = self.rect.x

#                 # constraints
#                 ramp_height = max(0, min(ramp_height, max_ramp_height))

#                 if 0 <= ramp.elevation <= 1:
#                     target_y = hitbox.y + TILESIZE * ramp.elevation - ramp_height
#                 else:
#                     hitbox_bottom_y = hitbox.y + hitbox.height
#                     target_y = hitbox_bottom_y - ramp_height

#                 if self.rect.bottom > target_y:  # check if the player collided with the actual ramp
#                     # adjust player height
#                     self.rect.bottom = target_y
#                     self.pos[1] = self.rect.y

#                     self._collision_types['bottom'] = True

#     def _handle_custom_ramps_colls(self, movement, dt: float, ramps: List[CustomRamp]) -> None:
#         for ramp in ramps:
#             hitbox = tile_rect(ramp)
#             ramp_collision = self.rect.colliderect(hitbox)

#             if ramp_collision:
#                 rel_x = self.rect.x - hitbox.x

#                 if ramp.orientation == TileType.RAMP_RIGHT:
#                     rel_x += self.rect.width
#                 rel_x = max(1, min(rel_x, ramp.size.x))  # sonst gibt es fehler
#                 ramp_height = ramp.height_data[rel_x - 1]  # mit height und unterschied zur current height kann man min_step_height einbauen

#                 # min. stepheight
#                 steppable = self._is_steppable_ramp(ramp)
#                 border_collision_threshold = 5
#                 if ramp.orientation == TileType.RAMP_RIGHT:
#                     rel_x_border = self.rect.x - (hitbox.x + TILESIZE)  # wie nah ist der Spieler an der Kante?
#                     if movement[0] < 0 and (0 < abs(rel_x_border) <= border_collision_threshold) and not steppable:
#                         ramp_height = 0
#                         self.rect.left = hitbox.right
#                         self._collision_types['left'] = True
#                         self.pos[0] = self.rect.x
#                 elif ramp.orientation == TileType.RAMP_LEFT:  # ! TODO bug beheben
#                     rel_x_border = self.rect.x - hitbox.x + self.rect.width  # wie nah ist der Spieler an der Kante?
#                     # print(rel_x_border, 0 < abs(rel_x_border) < border_collision_threshold, not steppable)
#                     if movement[0] > 0 and (0 < abs(rel_x_border) <= border_collision_threshold) and not steppable:
#                         ramp_height = 0
#                         self.rect.right = hitbox.left
#                         self._collision_types['right'] = True
#                         self.pos[0] = self.rect.x

#                 if ramp_height:
#                     adjust_height = TILESIZE + (ramp.size.y - TILESIZE)
#                     target_y = hitbox.y + adjust_height - ramp_height
#                     if self.rect.bottom > target_y:
#                         self.rect.bottom = target_y

#                         self.pos[1] = self.rect.y
#                         self._collision_types['bottom'] = True

#     def _handle_custom_tiles_colls(self, movement, dt: float, custom_tiles: List[CustomTile]) -> None:
#         for c_tile in custom_tiles:
#             hitbox = tile_rect(c_tile)
#             tile_collision = self.rect.colliderect(hitbox)

#             if tile_collision:
#                 rel_x = self.rect.x - hitbox.x

#                 if CUSTOM_TILES_ORIENTATION_DATA[c_tile.img_idx] == "left":
#                     rel_x += self.rect.w

#                 rel_x = max(1, min(rel_x, c_tile.size[0]))  # sonst gibt es fehler
#                 tile_height = CUSTOM_TILES_HEIGHT_DATA[c_tile.height_data_idx][rel_x - 1]  # mit height und unterschied zur current height kann man min_step_height einbauen
#                 steppable = self._is_steppable_custom_tile(c_tile, tile_height)

#                 if not steppable:
#                     border_collision_threshold = 5
#                     rel_x_border = self.rect.x - (hitbox.x + TILESIZE)  # wie nah ist der Spieler an der Kante?
#                     # print(1111111, rel_x_border, border_collision_threshold)
#                     if movement[0] < 0 and (0 < abs(rel_x_border) <= border_collision_threshold):
#                         tile_height = 0
#                         self.rect.left = hitbox.right
#                         self._collision_types['left'] = True
#                         self.pos[0] = self.rect.x
#                     elif self.rect.x < hitbox.x:
#                         rel_x_border = self.rect.x - hitbox.x + self.rect.width
#                         if movement[0] > 0 and (0 < abs(rel_x_border) <= border_collision_threshold):
#                             tile_height = 0
#                             self.rect.right = hitbox.left
#                             self._collision_types['right'] = True
#                             self.pos[0] = self.rect.x

#                 if tile_height:
#                     adjust_height = TILESIZE + (c_tile.size[1] - TILESIZE)
#                     target_y = hitbox.y + adjust_height - tile_height
#                     if self.rect.bottom > target_y:
#                         self.rect.bottom = target_y

#                         self.pos[1] = self.rect.y
#                         self._collision_types['bottom'] = True

#     def move(self, movement: Sequence[float], tiles: List[Tile], dt: float, noclip: bool = False):
#         if movement[0] != 0:
#             self.last_movement_dir[0] = movement[0]
#         if movement[1] != 0:
#             self.last_movement_dir[1] = movement[1]

#         self._last_pos = self.pos.copy()
#         self._last_collision_types = self._collision_types.copy()
#         self._collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}

#         if noclip:
#             self.pos[0] += movement[0] * dt
#             self.rect.x = int(self.pos[0])
#             self.pos[1] += movement[1] * dt
#             self.rect.y = int(self.pos[1])

#             return self._collision_types.copy()

#         normal_tiles = [tile_rect(t) for t in tiles if t.type == TileType.TILE]
#         ramps: List[Ramp] = [t for t in tiles if t.type in [TileType.RAMP_LEFT, TileType.RAMP_RIGHT]]
#         custom_ramps: List[CustomRamp] = [t for t in tiles if t.type is TileType.RAMP_CUSTOM]
#         custom_tiles: List[CustomTile] = [t for t in tiles if t.type is TileType.TILE_CUSTOM]

#         # handle collisions
#         self._handle_standart_colls(movement, dt, normal_tiles)
#         # self._handle_ramps_colls(movement, dt, ramps)
#         # self._handle_custom_ramps_colls(movement, dt, custom_ramps)
#         # self._handle_custom_tiles_colls(movement, dt, custom_tiles)

#         # ! TODO bugs fixen!
#         # ! 1. wenn man auf einer geraden linie läuft und springt, wird man beim laden zurück gebuggt.
#         # * 2. Manchmal werden falsche tiles als naheliegende erkannt, vorallem an chunkbordern.
#         # ! 3. wenn man gegen ein tile läuft, dass man nicht hoch gehen kann, bugt man andauernt nach links und rechts.
#         # * 4. Custom tiles werden nicht richtig gespeichert/geladen. Die Position im chunk ist zwar richtig, aber die collision position ist falsch
#         # * 5. speicher dauer verkürzen. Es dauert eine halbe Sekunde pro chunk manchmal.... (dann auch async machen, sodass man trotzdem noch weiter machen kann)

#         # return collisions
#         return self._collision_types.copy()

#     def update(self, dt: float) -> None:
#         self.animation.update(dt)

#         # if abs(self.vel.y) > 5:
#         #     self.set_state("jump_max")

#         if self._collision_types["bottom"] and self.get_state() != "idle":
#             self.set_state("idle")

#         if self.animation.new_img():  # TODO
#             self.mask = from_surface(self.animation.img())

#         # print(self.animation.over, self.animation.state)

#     def set_state(self, state: str) -> None:
#         self.animation.state = state

#     def get_state(self) -> str:
#         return self.animation.state

#     def render(self, surface: Surface, offset: Vector2 = Vector2(0)) -> None:
#         # img = self.animation.img()
#         # if img:
#         #     image_offset = Vector2(8, 0)
#         #     surface.blit(img, Vector2(self.rect.topleft) - offset - image_offset)

#         surface.blit(self.mask.to_surface(), (250, 250))
