from Scripts.CONFIG import *
from Scripts.tiles import *


class PhysicsEntity:
    __slots__ = ("pos", "_last_pos", "size", "vel", "rect", "min_step_height",
                 "_collision_types", "_last_collision_types")

    def __init__(self, pos: Vector2, size: Vector2) -> None:
        self.pos = pos
        self._last_pos = Vector2(0)
        self.size = size
        self.vel = Vector2(0)
        self.rect = Rect(pos.x, pos.y, size.x, size.y)
        self.min_step_height = 22  # in TILESIZE Größe gerechnet

        self._collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}
        self._last_collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}

    def _is_steppable(self, tile: Rect) -> bool:
        top_point = tile.y - tile.height
        # print(top_point - self.pos.y <= self.min_step_height * TILESIZE)
        return top_point - self.pos.y <= self.min_step_height * TILESIZE and self._last_collision_types["bottom"] and (self._last_collision_types["right"] or self._last_collision_types["left"])

    def _is_steppable_ramp(self, ramp: Ramp | CustomRamp) -> bool:
        if isinstance(ramp, Ramp):
            return TILESIZE * ramp.elevation <= self.min_step_height * TILESIZE
        return ramp.size.y <= self.min_step_height * TILESIZE

    def _is_steppable_custom_tile(self, c_tile: CustomTile, tile_height: float) -> bool:
        steppable = (TILESIZE - tile_height) < self.min_step_height * TILESIZE
        return steppable


class Player(PhysicsEntity):
    def __init__(self, pos: Vector2) -> None:
        super().__init__(pos, Vector2(TILESIZE // 2, TILESIZE))

    def _handle_standart_colls(self, movement, dt: float, normal_tiles: list[Tile]) -> None:
        self.pos[0] += movement[0] * dt
        self.rect.x = int(self.pos[0])
        tile_hit_list = collision_test(self.rect, normal_tiles)
        for t in tile_hit_list:
            if movement[0] > 0:
                self.rect.right = t.left
                self.collision_types['right'] = True
            elif movement[0] < 0:
                self.rect.left = t.right
                self.collision_types['left'] = True
            self.pos[0] = self.rect.x
            if self._is_steppable(t):  # das funktioniert nur wenn man an der linken kannte des spielers steht, dann auch nur bis dtmultiplier 2.5, ab 3.0 gehts net mehr TODO: FIXEN
                self.rect.bottom = t.top
                self.collision_types['bottom'] = True
                self.pos[1] = self.rect.y - 1  # kleiner offset, damit der Spieler nicht an der Kante stecken bleibt
        self.pos[1] += movement[1] * dt
        self.rect.y = int(self.pos[1])
        tile_hit_list = collision_test(self.rect, normal_tiles)
        for t in tile_hit_list:
            if movement[1] > 0:
                self.rect.bottom = t.top
                self.collision_types['bottom'] = True
            elif movement[1] < 0:
                self.rect.top = t.bottom
                self.collision_types['top'] = True
            self.pos[1] = self.rect.y

    def _handle_ramps_colls(self, movement, dt: float, ramps: list[Ramp]) -> None:
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
                        self.collision_types['left'] = True
                        self.pos[0] = self.rect.x
                elif ramp.type == TileType.RAMP_LEFT:
                    ramp_height = (TILESIZE * ramp.elevation) - rel_x * ramp.elevation

                    # min. stepheight
                    rel_x_border = self.rect.x - hitbox.x + self.rect.width  # wie nah ist der Spieler an der Kante?
                    if movement[0] > 0 and (0 < abs(rel_x_border) <= border_collision_threshold) and not steppable:
                        ramp_height = 0
                        self.rect.right = hitbox.left
                        self.collision_types['right'] = True
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

                    self.collision_types['bottom'] = True

    def _handle_custom_ramps_colls(self, movement, dt: float, ramps: list[CustomRamp]) -> None:
        for ramp in ramps:
            hitbox = tile_rect(ramp)
            ramp_collision = self.rect.colliderect(hitbox)

            if ramp_collision:
                rel_x = self.rect.x - hitbox.x

                if ramp.orientation == TileType.RAMP_RIGHT:
                    rel_x += self.rect.width
                rel_x = max(1, min(rel_x, ramp.size.x))  # sonst gibt es fehler
                ramp_height = ramp.height_data[rel_x - 1]  # mit height und unterschied zur current height kann man min_step_height einbauen

                # min. stepheight
                steppable = self._is_steppable_ramp(ramp)
                border_collision_threshold = 5
                if ramp.orientation == TileType.RAMP_RIGHT:
                    rel_x_border = self.rect.x - (hitbox.x + TILESIZE)  # wie nah ist der Spieler an der Kante?
                    if movement[0] < 0 and (0 < abs(rel_x_border) <= border_collision_threshold) and not steppable:
                        ramp_height = 0
                        self.rect.left = hitbox.right
                        self.collision_types['left'] = True
                        self.pos[0] = self.rect.x
                elif ramp.orientation == TileType.RAMP_LEFT:  # ! TODO bug beheben
                    rel_x_border = self.rect.x - hitbox.x + self.rect.width  # wie nah ist der Spieler an der Kante?
                    print(rel_x_border, 0 < abs(rel_x_border) < border_collision_threshold, not steppable)
                    if movement[0] > 0 and (0 < abs(rel_x_border) <= border_collision_threshold) and not steppable:
                        ramp_height = 0
                        self.rect.right = hitbox.left
                        self.collision_types['right'] = True
                        self.pos[0] = self.rect.x

                if ramp_height:
                    adjust_height = TILESIZE + (ramp.size.y - TILESIZE)
                    target_y = hitbox.y + adjust_height - ramp_height
                    if self.rect.bottom > target_y:
                        self.rect.bottom = target_y

                        self.pos[1] = self.rect.y
                        self.collision_types['bottom'] = True

    def _handle_custom_tiles_colls(self, movement, dt: float, custom_tiles: list[CustomTile]) -> None:
        for c_tile in custom_tiles:
            hitbox = tile_rect(c_tile)
            tile_collision = self.rect.colliderect(hitbox)

            if tile_collision:
                rel_x = self.rect.x - hitbox.x

                rel_x = max(1, min(rel_x, c_tile.size[0]))  # sonst gibt es fehler
                tile_height = c_tile.height_data[rel_x - 1]  # mit height und unterschied zur current height kann man min_step_height einbauen

                steppable = self._is_steppable_custom_tile(c_tile, tile_height)

                if not steppable:
                    border_collision_threshold = 5
                    rel_x_border = self.rect.x - (hitbox.x + TILESIZE)  # wie nah ist der Spieler an der Kante?
                    if movement[0] < 0 and (0 < abs(rel_x_border) <= border_collision_threshold) and not steppable:
                        tile_height = 0
                        self.rect.left = hitbox.right
                        self.collision_types['left'] = True
                        self.pos[0] = self.rect.x
                    elif self.rect.x < hitbox.x:
                        rel_x_border = self.rect.x - hitbox.x + self.rect.width
                        if movement[0] > 0 and (0 < abs(rel_x_border) <= border_collision_threshold) and not steppable:
                            tile_height = 0
                            self.rect.right = hitbox.left
                            self.collision_types['right'] = True
                            self.pos[0] = self.rect.x

                if tile_height:
                    adjust_height = TILESIZE + (c_tile.size[1] - TILESIZE)
                    target_y = hitbox.y + adjust_height - tile_height
                    if self.rect.bottom > target_y:
                        self.rect.bottom = target_y

                        self.pos[1] = self.rect.y
                        self.collision_types['bottom'] = True

    def move(self, movement: Sequence[float], tiles: list[Tile], dt: float, noclip: bool = False):
        self._last_pos = self.pos.copy()
        self._last_collision_types = self._collision_types.copy()
        self.collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}

        if noclip:
            self.pos[0] += movement[0] * dt
            self.rect.x = int(self.pos[0])
            self.pos[1] += movement[1] * dt
            self.rect.y = int(self.pos[1])

            return self.collision_types.copy()

        normal_tiles = [tile_rect(t) for t in tiles if t.type == TileType.TILE]
        ramps: list[Ramp] = [t for t in tiles if t.type in [TileType.RAMP_LEFT, TileType.RAMP_RIGHT]]
        custom_ramps: list[CustomRamp] = [t for t in tiles if t.type is TileType.RAMP_CUSTOM]
        custom_tiles: list[CustomTile] = [t for t in tiles if t.type is TileType.TILE_CUSTOM]

        # handle collisions
        self._handle_standart_colls(movement, dt, normal_tiles)
        self._handle_ramps_colls(movement, dt, ramps)
        self._handle_custom_ramps_colls(movement, dt, custom_ramps)
        self._handle_custom_tiles_colls(movement, dt, custom_tiles)

        # ! TODO bugs fixen!
        # ! 1. wenn man auf einer geraden linie läuft und springt, wird man beim laden zurück gebuggt.
        # ! 2. Manchmal werden falsche tiles als naheliegende erkannt, vorallem an chunkbordern.
        # ! 3. wenn man gegen ein tile läuft, dass man nicht hoch gehen kann, bugt man andauernt nach links und rechts.
        # * 4. Custom tiles werden nicht richtig gespeichert/geladen. Die Position im chunk ist zwar richtig, aber die collision position ist falsch
        # ! 5. speicher dauer verkürzen. Es dauert eine halbe Sekunde pro chunk manchmal.... (dann auch async machen, sodass man trotzdem noch weiter machen kann)

        # return collisions
        return self.collision_types.copy()
