import pygame
from pygame import Surface, Vector2
from typing import Hashable, Union, Iterable, Tuple


Coordinate = Union[Vector2, Tuple[int, int], Tuple[float, float]]


class Renderer:
    __slots__ = ("__groups", "__next_blit", "__active_groups")

    def __init__(self) -> None:
        self.__groups = set(("default",))
        self.__next_blit: dict[dict] = {"default": []}
        self.__active_groups: dict[dict] = {"default": True}

    def __reset_active_groups(self) -> None:
        self.__active_groups = {g: True for g in self.__groups}

    def __reset_blit_next(self) -> None:
        self.__next_blit = {elem: [] for elem in self.__groups}

    def __check_if_in_groups(self, group: Hashable) -> None:
        if not group in self.__groups:
            raise ValueError("The given group is not in the group pool.")

    def __combine_blits(self, blit_list: list) -> list:
        # fblits = [(d["source"], d["dest"]) for d in l] # geht nur, wenn es nur .blit gibt.
        fblits = []
        for d in blit_list:
            if "fblits" in d:
                fblits.extend(d["fblits"])
            else:
                fblits.append((d["source"], d["dest"]))
        return fblits

    def set_groups(self, *groups: Hashable) -> None:
        [self.__groups.add(elem) for elem in groups]
        self.__reset_blit_next()
        self.__reset_active_groups()

    def blit(self, source: Surface, dest: Coordinate, group: Hashable = "default", z: int = 0) -> None:
        self.__next_blit[group].append({"source": source, "dest": dest, "z": z})

    def fblits(self, fblits: Iterable[Tuple[Surface, Tuple]], group: Hashable = "default", z: int = 0) -> None:
        self.__next_blit[group].append({"fblits": fblits, "z": z})

    def toggle_group(self, group) -> bool:
        self.__check_if_in_groups(group)
        self.__active_groups[group] = not self.__active_groups[group]
        return self.__active_groups[group]

    def render_all(self, surface: Surface, special_flags: int = None) -> None:
        for group, data in self.__next_blit.items():
            if not self.__active_groups[group]:
                continue
            l = sorted(data, key=lambda x: x["z"])
            fblits = self.__combine_blits(l)
            surface.fblits(fblits, special_flags=special_flags)

        self.__reset_blit_next()

    def render_group(self, surface: Surface, group: Hashable, special_flags: int = None) -> None:
        self.__check_if_in_groups(group)
        if not self.__active_groups[group]:
            return

        l = sorted(self.__next_blit[group], key=lambda x: x["z"])
        fblits = self.__combine_blits(l)
        surface.fblits(fblits, special_flags=special_flags)

        self.__next_blit[group].clear()


class GameTemplate:
    __slots__ = ("screen", "clock", "time", "renderer")

    def __init__(self, size: Coordinate, flags=0, depth=0, display=0, vsync=0):
        self.screen = pygame.display.set_mode(size, flags=flags, depth=depth, display=display, vsync=vsync)
        self.clock = pygame.time.Clock()
        self.time = .0

        self.renderer = Renderer()

    @property
    def w(self) -> int: return self.screen.get_width()

    @property
    def h(self) -> int: return self.screen.get_height()

    def update(self) -> float:
        self.time += (dt := self.clock.tick(0) * .001)
        return dt

    def render(self) -> None: raise NotImplementedError("render method is not implemented")
    def handle_events(self) -> None: raise NotImplementedError("handle_events method is not implemented")

    def run(self) -> None:
        while True:
            self.handle_events()
            self.update()
            self.render()
