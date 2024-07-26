import pygame
from pygame import Rect, Surface, Color

from functools import lru_cache
from typing import Callable, Iterable, Dict, List, Tuple

pygame.font.init()
_default_font = pygame.sysfont.SysFont("arial", 18)


@lru_cache(maxsize=1)
def get_ui_manager() -> "_Manager":
    return _Manager()


class _Manager:
    def __init__(self) -> None:
        self.widgets: Dict[str, List[Widget]] = {
            "buttons": [],
            "labels": []}

    def add(self, widget: "Widget") -> None:
        if isinstance(widget, Button):
            self.widgets["buttons"].append(widget)
        if isinstance(widget, Label):
            self.widgets["labels"].append(widget)

    def render(self, surf):
        [w.render(surf) for w in self.widgets["buttons"]]
        [w.render(surf) for w in self.widgets["labels"]]

    def update(self, dt: float):
        mPos = pygame.mouse.get_pos()
        mjpress = pygame.mouse.get_just_pressed()
        mjrelease = pygame.mouse.get_just_released()

        for w in self.widgets["buttons"]:
            if w.rect.collidepoint(mPos):
                if mjpress[0]:
                    w._clicked()
                if mjrelease[0]:
                    w._released()


class Widget:
    def __init__(self, r) -> None:
        get_ui_manager().add(self)

        self.rect = r

    def render(self, surf: Surface):
        pygame.draw.rect(surf, "white", self.rect)


class Button(Widget):
    def __init__(self, r, image: Surface = None) -> None:
        super().__init__(r)

        self.__image = image

        self.__on_click: Callable = None
        self.__on_click_params: Iterable = None
        self.__on_release: Callable = None
        self.__on_release_params: Iterable = None

    # region button properties
    @property
    def on_click(self) -> Callable: return self.__on_click

    @on_click.setter
    def on_click(self, val: Callable) -> None: self.__on_click = val

    @property
    def on_click_params(self) -> Iterable: return self.__on_click_params

    @on_click_params.setter
    def on_click_params(self, val: Iterable) -> None: self.__on_click_params = val

    @property
    def on_release(self) -> Callable: return self.__on_release

    @on_release.setter
    def on_release(self, val: Callable) -> None: self.__on_release = val

    @property
    def on_release_params(self) -> Iterable: return self.__on_release_params

    @on_release_params.setter
    def on_release_params(self, val: Iterable) -> None: self.__on_release_params = val
    # endregion

    def _clicked(self) -> None:
        self.__on_click(* self.__on_click_params)

    def _released(self) -> None:
        self.__on_release(* self.__on_release_params)

    def render(self, surface: Surface) -> None:
        ...


class Label(Widget):
    def __init__(self, r, font: pygame.Font = None, text: str = None) -> None:
        super().__init__(r)

        if font:
            self.__font = font
        else:
            self.__font = _default_font
        self.__text: str = text
        self.__clip_text = False

    # region label properties
    @property
    def text(self) -> str: return self.__text

    @text.setter
    def text(self, val: str): self.__text = val

    @property
    def clip_text(self) -> bool: return self.__clip_text

    @clip_text.setter
    def clip_text(self, val: bool) -> None: self.__clip_text = val
    # endregion

    def render(self, surf: Surface) -> None:
        super().render(surf)
        txt_surf = self.__font.render(self.text, True, (0, 0, 0))
        if self.__clip_text:
            txt_r = txt_surf.get_rect()
            clip_r = Rect(0, 0, min(self.rect.w, txt_r.w), min(self.rect.h, txt_r.h))
            txt_surf = txt_surf.subsurface(clip_r)
        surf.blit(txt_surf, self.rect.topleft)


def make_icon_from_letter(letter: str, size: Tuple, color: Color, bg_color: Color) -> Surface:
    surf = Surface(size)
    surf.fill(bg_color)

    if len(letter) > 1:
        letter = letter[0]

    font = pygame.font.SysFont("arial", max(0, min(size[1], size[0])))

    l = font.render(letter, True, color)

    center_offset = (size[0]/2 - l.get_width()/2, size[1]/2 - l.get_height()/2)
    surf.blit(l, center_offset)
    return surf
