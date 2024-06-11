import pygame
from typing import Callable, Any


class TimerManager:
    timers: list["Timer"] = []

    @staticmethod
    def update() -> None:
        [t.update() for t in TimerManager.timers]

    @staticmethod
    def add(timer: "Timer") -> None:
        TimerManager.timers.append(timer)

    @staticmethod
    def extend(timers: list["Timer"]) -> None:
        TimerManager.timers.extend(timers)

    @staticmethod
    def remove(timer: "Timer") -> None:
        if timer in TimerManager.timers:
            TimerManager.timers.remove(timer)


class Timer:
    __slots__ = ("duration", "repeat", "start_time", "active", "_start_hooks", "_end_hooks")

    def __init__(self, duration: float, repeat: bool = None, autostart: bool = False) -> None:
        self.duration = duration
        self.repeat = repeat
        self.start_time = 0
        self.active = False
        self._start_hooks: list[Callable[..., Any]] = []
        self._end_hooks: list[Callable[..., Any]] = []
        # Eine Queue hier könnte scheclt sein, falls der timer auf autostart ist. Queue habe ich nur genommen für FIFO (First in, First out). Sonst Liste Nehmen

        if autostart:
            self.activate()

        TimerManager.add(self)

    def __bool__(self):  # wird gecalled wenn man if timer: macht. (timer = instance von Timer). Dann muss man nicht mehr timer.active schreiben
        return self.active

    def remove(self) -> None:
        TimerManager.remove(self)

    def activate(self):
        self.active = True
        self.start_time = pygame.time.get_ticks()
        self._execute_hooks(self._start_hooks)

    def end(self) -> None:
        self._execute_hooks(self._end_hooks)

    def deactivate(self):
        self.active = False
        self.start_time = 0
        if self.repeat:
            self.activate()

    def update(self, /):
        if pygame.time.get_ticks() - self.start_time >= self.duration:
            if self.start_time != 0:
                self.end()
            self.deactivate()

    def add_start_hook(self, hook: Callable):
        self._start_hooks.append(hook)
        # print("Added start hook:", hook.__name__)

    def add_end_hook(self, hook: Callable):
        self._end_hooks.append(hook)
        # print("Added end hook:", hook.__name__)

    def _execute_hooks(self, hooks: list[Callable[..., Any]]) -> None:
        for hook in hooks:
            hook()


def call_on_timer_start(timer: Timer):
    def decorator(func: Callable):
        timer.add_start_hook(func)
        return func
    return decorator


def call_on_timer_end(timer: Timer):
    def decorator(func: Callable):
        timer.add_end_hook(func)
        return func
    return decorator


if __name__ == "__main__":
    pygame.init()

    timermanager = TimerManager()
    timer = Timer(2000)

    @call_on_timer_start(timer)
    def test1():
        print("test1 called")

    @call_on_timer_end(timer)
    def test2():
        print("test2 called")

    screen = pygame.display.set_mode((100, 100))
    clock = pygame.time.Clock()
    timer.activate()
    while True:
        dt = clock.tick(60) * 0.001
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                exit()
        timermanager.update()
