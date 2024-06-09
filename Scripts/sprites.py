from Scripts.CONFIG import *
from Scripts.utils import load_image, surf_is_black


def cut_spritesheet(path_or_image: str | Surface, img_size: Vector2, max_frames: int = -1) -> list[Surface]:
    if isinstance(path_or_image, str):
        sheet = load_image(path_or_image)
    elif isinstance(path_or_image, Surface):
        sheet = path_or_image
    else:
        raise TypeError("path_or_image has to be of type <str> or <pygame.Surface>")

    ret = []
    sheet_size = Vector2(sheet.get_size())
    i = 0

    for y in range(int(sheet_size.y / img_size.y)):
        for x in range(int(sheet_size.x / img_size.x)):
            img = sheet.subsurface(Rect(x * img_size.x, y * img_size.y, img_size.x, img_size.y))
            i += 1
            if not surf_is_black(img):
                ret.append(img)
            if i > max_frames and max_frames > 0:
                break

    return ret


def cut_spritesheet_row(path_or_image: str | Surface, img_size: Vector2, row_index: int, max_frames: int = -1) -> list[Surface]:
    if isinstance(path_or_image, str):
        sheet = load_image(path_or_image)
    elif isinstance(path_or_image, Surface):
        sheet = path_or_image
    else:
        raise TypeError("path_or_image has to be of type <str> or <pygame.Surface>")

    ret = []
    sheet_size = Vector2(sheet.get_size())
    i = 0

    for x in range(int(sheet_size.x / img_size.x)):
        img = sheet.subsurface(Rect(x * img_size.x, row_index * img_size.y, img_size.x, img_size.y))
        i += 1
        if not surf_is_black(img):
            ret.append(img)
        if i > max_frames and max_frames > 0:
            break

    return ret


class Animation:
    def __init__(self) -> None:
        self.states: dict[str, list[Surface]] = {}
        self.states_looping: dict[str, bool] = {}

        self.__state: str = None
        self.index: float = 0.0

    def add_state(self, state: str, surfs: list[Surface], looping: bool = True) -> None:
        if state not in self.states:
            self.states[state] = surfs
            self.states_looping[state] = looping

    @property
    def state(self) -> str:
        return self.__state

    @state.setter
    def state(self, state: str) -> None:
        self.__state = state

    def update(self, dt: float, change: float = 1.0) -> None:
        if self.states_looping[self.__state]:  # looping
            self.index = (self.index + change * dt) % len(self.states[self.__state])
        else:  # nicht looping
            self.index = min(self.index + change * dt, len(self.states[self.__state]) - 1)

    def img(self) -> Surface:
        return self.states[self.__state][int(self.index)]
