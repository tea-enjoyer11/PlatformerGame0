import pygame
from pygame import Rect, Surface, Color

from functools import lru_cache
from typing import Callable, Iterable, Dict, List, Tuple, Set

pygame.font.init()
_default_font = pygame.sysfont.SysFont("arial", 18)


UI_CLICK = pygame.USEREVENT + 0
UI_RELEASE = pygame.USEREVENT + 1
UI_HOVER_ENTER = pygame.USEREVENT + 2
UI_HOVER = pygame.USEREVENT + 3
UI_HOVER_EXIT = pygame.USEREVENT + 4


@lru_cache(maxsize=1)
def get_ui_manager() -> "_Manager":
    return _Manager()


class _Manager:
    def __init__(self) -> None:
        self.widgets: Dict[str, List[Widget]] = {
            "buttons": [],
            "labels": []
        }

    def add(self, widget: "Widget") -> None:
        if isinstance(widget, Button):
            self.widgets["buttons"].append(widget)
        if isinstance(widget, Label):
            self.widgets["labels"].append(widget)

    def render_ui(self, surf):
        [w.render(surf) for w in self.widgets["buttons"]]
        [w.render(surf) for w in self.widgets["labels"]]

    def update(self, dt: float):
        mPos = pygame.mouse.get_pos()
        mjpress = pygame.mouse.get_just_pressed()
        mjrelease = pygame.mouse.get_just_released()

        for w in self.widgets["buttons"]:
            w_hover = w.rect.collidepoint(mPos)

            # ! Achtung: was, wenn zwei Widgets übereinander liegen???
            if w_hover:
                if w._hover_state == 0:
                    w._hover_state = 1
                if w._hover_state == 1:
                    w._hover_state = 2
            else:
                if w._hover_state == 2:
                    w._hover_state = 3
                if w._hover_state == 3:
                    w._hover_state = 0

            if w._hover_state == 1:
                ev = pygame.event.Event(UI_HOVER_ENTER, attr1="click", ui_element=w)
                pygame.event.post(ev)
            if w._hover_state == 2:
                ev = pygame.event.Event(UI_HOVER, attr1="click", ui_element=w)
                pygame.event.post(ev)
            if w._hover_state == 3:
                ev = pygame.event.Event(UI_HOVER_EXIT, attr1="click", ui_element=w)
                pygame.event.post(ev)

            if w_hover:
                if mjpress[0]:
                    ev = pygame.event.Event(UI_CLICK, attr1="click", ui_element=w)
                    pygame.event.post(ev)
                if mjrelease[0]:
                    ev = pygame.event.Event(UI_RELEASE, attr1="release", ui_element=w)
                    pygame.event.post(ev)

    def process_event(self, event: pygame.event.Event) -> None: ...


# ist das überhaupt nötig?
class WidgetGroup:
    def __init__(self) -> None:
        self.__widgets: List[Widget] = []

    def add(self, widget: "Widget") -> None:
        self.__widgets.append(widget)

    def remove(self, widget: "Widget") -> None:
        if widget in self.__widgets:
            self.__widgets.remove(widget)
        #     return
        # raise ValueError("Widget not in WidgetGroup")


class Widget:
    def __init__(self, rect, image: pygame.Surface = None) -> None:
        get_ui_manager().add(self)

        self.rect = rect
        self._image = image
        self._blendmode = pygame.BLENDMODE_NONE

        self._blit_data = [self._image, self.rect, None, self._blendmode]  # 1. None = pygame.Surface

        self._hover_state = 0  # 0: nix, 1: enter, 2: hover, 3: exit

    # region Widget properties
    @property
    def blendmode(self) -> int:
        return self._blendmode

    @blendmode.setter
    def blendmode(self, blendmode: int) -> None:
        self._blendmode = blendmode
        self._blit_data[3] = blendmode
    # endregion

    def render(self, surf: Surface):
        pygame.draw.rect(surf, "white", self.rect)


class Button(Widget):
    def __init__(self, r, image: Surface = None) -> None:
        super().__init__(r, image)

    def render(self, surface: Surface) -> None:
        # super().render(surface)
        if self._image:
            surface.blit(*self._blit_data)
        else:
            pygame.draw.rect(surface, "white", self.rect)


class Label(Widget):
    def __init__(self, r, font: pygame.Font = None, text: str = None) -> None:
        super().__init__(r)

        if font:
            self._font = font
        else:
            self._font = _default_font
        self._text: str = text
        self._clip_text = False

    # region Label properties
    @property
    def text(self) -> str: return self._text

    @text.setter
    def text(self, val: str): self._text = val

    @property
    def clip_text(self) -> bool: return self._clip_text

    @clip_text.setter
    def clip_text(self, val: bool) -> None: self._clip_text = val
    # endregion

    def render(self, surf: Surface) -> None:
        super().render(surf)
        txt_surf = self._font.render(self.text, True, (0, 0, 0))
        if self._clip_text:
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
