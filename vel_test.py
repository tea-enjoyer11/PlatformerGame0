import pygame

from Scripts.utils import draw_text

pygame.init()
display = pygame.display.set_mode((640, 480))
clock = pygame.time.Clock()
GRAY = pygame.Color('gray12')
display_width, display_height = display.get_size()

x = display_width * 0.45
y = display_height * 0.8

x_change = 0
y_change = 0
accel_x = 0
accel_y = 0
max_speed = 6


def sign(a): return (a > 0) - (a < 0)


crashed = False
FRICTION = 0.01
while not crashed:
    dt = clock.tick(60) * 0.001

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            crashed = True

    keys = pygame.key.get_pressed()

    # handle left and right movement
    if keys[pygame.K_a] and not keys[pygame.K_d]:
        x_change = max(x_change - 1 * dt, -max_speed)
    elif keys[pygame.K_d] and not keys[pygame.K_a]:
        x_change = min(x_change + 1 * dt, max_speed)
    else:
        x_change -= x_change * (1 - FRICTION) * dt

    # handle up and down movement
    if keys[pygame.K_w] and not keys[pygame.K_s]:
        y_change = max(y_change - 1 * dt, -max_speed)
    elif keys[pygame.K_s] and not keys[pygame.K_w]:
        y_change = min(y_change + 1 * dt, max_speed)
    else:
        y_change -= y_change * (1 - FRICTION) * dt

    x += x_change  # Move the object.
    y += y_change

    if keys[pygame.K_r]:
        x_change = 0
        y_change = 0
        x = display_width * 0.45
        y = display_height * 0.8

    display.fill(GRAY)
    pygame.draw.rect(display, (0, 120, 250), (x, y, 20, 40))

    draw_text(display, f"FPS: {clock.get_fps():.2f} DT: {dt}", (10, 10))
    draw_text(display, f"VEL: {x_change:.2f}, {y_change:.2f} FRICTION: {(1 - FRICTION) * dt}", (10, 30))

    pygame.display.update()
