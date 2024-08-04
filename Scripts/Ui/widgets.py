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
UI_SLIDER_HORIZONTAL_MOVED = pygame.USEREVENT + 5
UI_SLIDER_VERTICAL_MOVED = pygame.USEREVENT + 6


def get_event_name(e) -> str:
    d = {
        UI_CLICK: "UI_CLICK", UI_RELEASE: "UI_RELEASE",
        UI_HOVER_ENTER: "UI_HOVER_ENTER", UI_HOVER: "UI_HOVER",
        UI_HOVER_EXIT: "UI_HOVER_EXIT", UI_SLIDER_HORIZONTAL_MOVED: "UI_SLIDER_HORIZONTAL_MOVED",
        UI_SLIDER_VERTICAL_MOVED: "UI_SLIDER_VERTICAL_MOVED"
    }
    return d[e]


@lru_cache(maxsize=1)
def get_ui_manager() -> "_Manager":
    return _Manager()


def post_event(type: int, **kwargs) -> None:
    ev = pygame.event.Event(type, name=get_event_name(type), **kwargs)
    pygame.event.post(ev)


class _Manager:
    def __init__(self) -> None:
        self.widgets: List[Widget] = []

        self.last_topmost_widget: Widget = None
        self.topmost_widget: Widget = None

    def add(self, widget: "Widget") -> None:
        self.widgets.append(widget)
        self.widgets.sort(key=lambda w: w.z_index, reverse=True)

    def render_ui(self, surf: Surface) -> None:
        for widget in sorted(self.widgets, key=lambda w: w.z_index, reverse=False):
            widget.render(surf)

    def render_debug(self, surf: Surface) -> None:
        if self.last_topmost_widget:
            r = self.last_topmost_widget.rect.copy()
            r.inflate_ip(25, 25)
            s = pygame.Surface(r.size)
            s.fill((255, 0, 0))
            s.set_alpha(100)
            surf.blit(s, r, special_flags=pygame.BLEND_ADD)

        if self.topmost_widget:
            r = self.topmost_widget.rect.copy()
            r.inflate_ip(25, 25)
            s = pygame.Surface(r.size)
            s.fill((0, 255, 0))
            s.set_alpha(100)
            surf.blit(s, r, special_flags=pygame.BLEND_ADD)

    def update(self, dt: float):
        mPos = pygame.mouse.get_pos()
        mpress = pygame.mouse.get_pressed()
        mjpress = pygame.mouse.get_just_pressed()
        mjrelease = pygame.mouse.get_just_released()

        self.last_topmost_widget = self.topmost_widget

        none_hoverd = True
        for widget in self.widgets:
            if widget.rect.collidepoint(mPos):
                self.topmost_widget = widget
                none_hoverd = False
                break
        if none_hoverd:
            self.topmost_widget = None

        for widget in self.widgets:
            # region Hoverlogic (vllt nicht allzu schön geschrieben)
            if widget == self.topmost_widget:
                if widget._hover_state == 0:
                    widget._hover_state = 1
                elif widget._hover_state == 1:
                    widget._hover_state = 2
            else:
                if widget._hover_state == 2:
                    widget._hover_state = 3
                elif widget._hover_state == 3:
                    widget._hover_state = 0

            if widget._hover_state == 1:
                post_event(UI_HOVER_ENTER, ui_element=widget)
            elif widget._hover_state == 2:
                post_event(UI_HOVER, ui_element=widget)
            elif widget._hover_state == 3:
                post_event(UI_HOVER_EXIT, ui_element=widget)
            # endregion

        if isinstance(self.topmost_widget, Button):
            if mjpress[0]:
                post_event(UI_CLICK, ui_element=widget)
            if mjrelease[0]:
                post_event(UI_RELEASE, ui_element=widget)

        if isinstance(self.topmost_widget, SliderHorizontal):
            if mpress[0]:
                self.topmost_widget.update(*mPos)
        if isinstance(self.last_topmost_widget, SliderVertical):
            if mpress[0]:
                self.last_topmost_widget.update(*mPos)

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
    def __init__(self, rect, image: pygame.Surface = None, z_index: int = 0) -> None:

        self.z_index = z_index
        self.rect = rect
        self._image = image
        self._blendmode = pygame.BLENDMODE_NONE

        self._blit_data = [self._image, self.rect, None, self._blendmode]  # 1. None = pygame.Surface

        self._hover_state = 0  # 0: nix, 1: enter, 2: hover, 3: exit

        get_ui_manager().add(self)

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
    def __init__(self, r, image: Surface = None, z_index: int = 0) -> None:
        super().__init__(r, image, z_index)

    def render(self, surface: Surface) -> None:
        # super().render(surface)
        if self._image:
            surface.blit(*self._blit_data)
        else:
            pygame.draw.rect(surface, "white", self.rect)


class Label(Widget):
    def __init__(self, r, font: pygame.Font = None, text: str = None, z_index: int = 0) -> None:
        super().__init__(r, None, z_index)

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


class SliderHorizontal(Widget):
    def __init__(self, rect, min: float, max: float, image: Surface = None, percentage: float = .5) -> None:
        super().__init__(rect, image)

        self._min = min
        self._max = max
        self._percent = percentage

    def val(self) -> float:
        return self._min + (self._max - self._min) * self._percent

    def update(self, mx: int, my: int) -> None:
        self.calc_new_percent(mx)

    def calc_new_percent(self, mx: int) -> None:
        rel_x = max(min(mx - self.rect.x, self.rect.w), 0)
        self._percent = rel_x / self.rect.w
        post_event(UI_SLIDER_HORIZONTAL_MOVED, ui_element=self, value=self.val())

    def render(self, surface: Surface) -> None:
        super().render(surface)

        # select slider
        x = self.rect.x + self.rect.w * self._percent
        start = (x, self.rect.y)
        end = (x, self.rect.y + self.rect.h)
        pygame.draw.line(surface, (0, 0, 0), start, end, width=3)


class SliderVertical(Widget):
    def __init__(self, rect, min: float, max: float, image: Surface = None, percentage: float = .5) -> None:
        super().__init__(rect, image)

        self._min = min
        self._max = max
        self._percent = percentage

    def val(self) -> float:
        return self._min + (self._max - self._min) * self._percent

    def update(self, mx: int, my: int) -> None:
        self.calc_new_percent(my)

    def calc_new_percent(self, my: int) -> None:
        rel_y = max(min(my - self.rect.y, self.rect.h), 0)
        self._percent = rel_y / self.rect.h
        post_event(UI_SLIDER_VERTICAL_MOVED, ui_element=self, value=self.val())

    def render(self, surface: Surface) -> None:
        super().render(surface)

        # select slider
        y = self.rect.y + self.rect.h * self._percent
        start = (self.rect.x, y)
        end = (self.rect.x + self.rect.w, y)
        pygame.draw.line(surface, (0, 0, 0), start, end, width=3)


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


def make_icon_from_text(text: str, size: Tuple, color: Color, bg_color: Color) -> Surface:
    surf = Surface(size)
    surf.fill(bg_color)

    if len(text) > 1:
        s = max(0, min(size[1], size[0])) / len(text) * 1.5
    else:
        s = max(0, min(size[1], size[0]))
    font = pygame.font.SysFont("arial", int(s))

    l = font.render(text, True, color)

    center_offset = (size[0]/2 - l.get_width()/2, size[1]/2 - l.get_height()/2)
    surf.blit(l, center_offset)
    return surf
