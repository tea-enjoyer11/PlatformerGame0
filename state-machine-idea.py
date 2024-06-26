import pygame


class GameState:
    def __init__(self, name, app):
        self.name = name
        self.app = app

    def handle_events(self, event):
        pass

    def update(self):
        pass

    def draw(self):
        pass


class GamestateManager:
    def __init__(self, app):
        self.app = app
        self.states = {}
        self.state = None

    def add(self, state):
        self.states[state.name] = state

    def set_state(self, name):
        self.state = self.states[name]

    def update(self):
        if self.state is not None:
            self.state.update()

    def draw(self):
        if self.state is not None:
            self.state.draw()

    def handle_events(self, event):
        if self.state is not None:
            self.state.handle_events(event)


class MenuState(GameState):
    def __init__(self, name, app):
        super().__init__(name, app)

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.app.game_state_manager.set_state("game")

    def update(self):
        pass

    def draw(self):
        self.app.screen.fill("red")


class PlayingState(GameState):
    def __init__(self, name, app):
        super().__init__(name, app)

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.app.game_state_manager.set_state("menu")

    def update(self):
        pass

    def draw(self):
        self.app.screen.fill("blue")


class App:
    def __init__(self):
        pygame.init()

        self.width, self.height = self.size = (800, 600)

        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption("My Game")

        self.game_state_manager = GamestateManager(self)

        self.game_state_manager.add(MenuState("menu", self))
        self.game_state_manager.add(PlayingState("game", self))

        self.game_state_manager.set_state("menu")

        self.fps = 60

        self.clock = pygame.time.Clock()
        self.running = True

        self.delta_time = 0

    def run(self):
        while self.running:
            self.delta_time = self.clock.tick(self.fps) / 1000.0
            self.events()
            self.update()
            self.draw()

    def events(self):
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                self.running = False

            self.game_state_manager.handle_events(event)

    def update(self):
        self.game_state_manager.update()
        pass

    def draw(self):
        self.screen.fill("white")

        self.game_state_manager.draw()
        pygame.display.flip()


if __name__ == "__main__":
    App().run()
