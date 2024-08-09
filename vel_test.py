import pygame
import sys

# Initialize Pygame
pygame.init()
pygame.font.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SIZE = 50
ACCELERATION = 50
FRICTION = -0.2
MAX_SPEED = 5000

# Colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)

# Screen setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Player properties
player_pos = pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
player_velocity = pygame.Vector2(0, 0)
player_acceleration = pygame.Vector2(0, 0)

# Clock for framerate independence
clock = pygame.time.Clock()

font = pygame.font.SysFont("arial", 18)


def handle_input():
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player_acceleration.x = -ACCELERATION
    elif keys[pygame.K_RIGHT]:
        player_acceleration.x = ACCELERATION
    else:
        player_acceleration.x = 0

    if keys[pygame.K_UP]:
        player_acceleration.y = -ACCELERATION
    elif keys[pygame.K_DOWN]:
        player_acceleration.y = ACCELERATION
    else:
        player_acceleration.y = 0


def update(dt):
    global player_velocity, player_pos

    # Apply acceleration
    player_velocity += player_acceleration

    # Apply friction
    player_velocity += player_velocity * FRICTION

    if 0 < player_velocity.x < 0.1 or -0.1 < player_velocity.x < 0:
        player_velocity.x = 0
    if 0 < player_velocity.y < 0.1 or -0.1 < player_velocity.y < 0:
        player_velocity.y = 0

    # Cap the speed
    if player_velocity.length() > MAX_SPEED:
        player_velocity.scale_to_length(MAX_SPEED)

    # Update player position
    player_pos += player_velocity * dt

    # Keep the player on screen
    player_pos.x = max(0, min(SCREEN_WIDTH - PLAYER_SIZE, player_pos.x))
    player_pos.y = max(0, min(SCREEN_HEIGHT - PLAYER_SIZE, player_pos.y))


def draw():
    screen.fill(WHITE)
    pygame.draw.rect(screen, BLUE, (*player_pos, PLAYER_SIZE, PLAYER_SIZE))
    screen.blit(font.render(f"{clock.get_fps()}", True, (0, 0, 0)), (0, 0))
    screen.blit(font.render(f"{player_velocity}", True, (0, 0, 0)), (0, 25))
    pygame.display.flip()


def main():
    while True:
        dt = clock.tick(30) / 1000  # Convert to seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()

        handle_input()
        update(dt)
        draw()


if __name__ == '__main__':
    main()
