import pygame
from typing import Callable


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
    __slots__ = ("duration", "func", "repeat", "start_time", "active")

    def __init__(self, duration: float, func: Callable = None, repeat: bool = None, autostart: bool = False) -> None:
        self.duration = duration
        self.func = func
        self.repeat = repeat
        self.start_time = 0
        self.active = False

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

    def deactivate(self):
        self.active = False
        self.start_time = 0
        if self.repeat:
            self.activate()

    def update(self, /):
        if pygame.time.get_ticks() - self.start_time >= self.duration:
            if self.func and self.start_time != 0:
                self.func()
            self.deactivate()
