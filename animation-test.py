import pygame
from Scripts.sprites import cut_spritesheet_row, Vector2, Animation
from Scripts.timer import Timer, TimerManager, call_on_timer_end

pygame.init()

screen = pygame.display.set_mode((200, 200))
clock = pygame.time.Clock()

timermanager = TimerManager()
timer = Timer(4 * 12 * 9, repeat=False)
timer2 = Timer(2 * 12 * 9, repeat=False)
animation = Animation()
path = "assets/entities/AnimationSheet_Character.png"
s = Vector2(32)

animation.add_state("idle", cut_spritesheet_row(path, s, 0), frame_time=3)
animation.add_state("idle_alt", cut_spritesheet_row(path, s, 1), frame_time=3)
animation.add_state("walk", cut_spritesheet_row(path, s, 2), frame_time=6)
animation.add_state("run", cut_spritesheet_row(path, s, 3), frame_time=12)
animation.add_state("jump_init", cut_spritesheet_row(path, s, 5, max_frames=4), looping=False, frame_time=12)
animation.add_state("jump_fall", cut_spritesheet_row(path, s, 5, max_frames=2, starting_frame=5), looping=False, frame_time=12)
animation.add_state("jump_complete", cut_spritesheet_row(path, s, 5), frame_time=12)

animation.state = "idle"


@call_on_timer_end(timer)
def t():
    print(1)
    animation.state = "jump_fall"
    timer2.activate()


@call_on_timer_end(timer2)
def t():
    print(2)
    animation.state = "idle"


while True:
    screen.fill((25, 100, 0))
    dt = clock.tick(0) * 0.001
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                animation.state = "idle"
            if event.key == pygame.K_2:
                animation.state = "walk"
            if event.key == pygame.K_3:
                animation.state = "run"
            if event.key == pygame.K_4:
                animation.state = "jump_init"
                timer.activate()
            if event.key == pygame.K_5:
                animation.state = "jump_fall"
            if event.key == pygame.K_6:
                animation.state = "jump_complete"

    timermanager.update()
    animation.update(dt)
    screen.blit(pygame.transform.scale(animation.img(), (200, 200)), (0, 0))
    pygame.display.flip()
