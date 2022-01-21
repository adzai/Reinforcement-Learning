import pygame
import sys
import numpy as np
from environment import Environment
from constants import REWARD, SQUARE_TYPE

SCREEN_WIDTH = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_WIDTH + SCREEN_WIDTH // 10))
width = SCREEN_WIDTH // 16
snake_width = 25
score_line_rect = pygame.Rect(0, SCREEN_WIDTH + 1, SCREEN_WIDTH + SCREEN_WIDTH // 10, 1)


def ai_play(args):
    if args.env_size > 16 or args.env_size < 3:
        print("env_size argument must be >=3 and <=16")
        sys.exit(3)
    if args.q_table is None:
        print(
            "Must provide --q_table argument with path to a q table saved as a numpy array."
        )
        sys.exit(2)
    try:
        q_table = np.load(args.q_table)
        print("Loaded Q table:", args.q_table)
    except Exception as e:
        print(f"Couldn't load q table {args.q_table}: {e}")
        sys.exit(3)
    x_border_rect = pygame.Rect(0, width * args.env_size, width * args.env_size, 1)
    y_border_rect = pygame.Rect(width * args.env_size, 0, 1, width * args.env_size)
    MOVEEVENT = pygame.USEREVENT + 1
    update_interval = args.speed
    pygame.time.set_timer(MOVEEVENT, update_interval)
    pygame.init()
    pygame.font.init()
    score_font = pygame.font.SysFont("arial", 30)
    env = Environment(args.env_size, args.depth)
    state = env.reset()
    done = False
    running = True
    while running:
        if not done:
            for e in pygame.event.get():
                if e.type == MOVEEVENT:
                    action = np.argmax(q_table[state, :])
                    new_state, _, done = env.step(action)
                    state = new_state

        screen.fill((192, 192, 192))
        display_game_grid(env, x_border_rect, y_border_rect, score_font)
        if done:
            textsurface = score_font.render(
                "Game over!",
                True,
                (200, 0, 0),
            )
            screen.blit(
                textsurface,
                (
                    SCREEN_WIDTH // 2 + SCREEN_WIDTH // 10,
                    SCREEN_WIDTH + SCREEN_WIDTH // 20,
                ),
            )
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
        pygame.display.flip()


def display_game_grid(env, x_rect, y_rect, score_font):
    head = env.snake.body[0]
    for y, row in enumerate(env.grid):
        for x, _ in enumerate(row):
            if head.y == y and head.x == x:
                rect = pygame.Rect(
                    head.x * width,
                    head.y * width,
                    width,
                    width,
                )
                pygame.draw.rect(screen, (200, 0, 0), rect)
            elif env.grid[y][x] == SQUARE_TYPE.snake:
                rect = pygame.Rect(
                    x * width + 10, y * width + 10, snake_width, snake_width
                )
                pygame.draw.rect(screen, (34, 139, 34), rect)
            elif env.grid[y][x] == SQUARE_TYPE.food:
                rect = pygame.Rect(
                    x * width + 10,
                    y * width + 10,
                    snake_width,
                    snake_width,
                )
                pygame.draw.rect(screen, (0, 0, 255), rect)

        pygame.draw.rect(screen, (112, 112, 112), score_line_rect)
        pygame.draw.rect(screen, (0, 0, 0), x_rect)
        pygame.draw.rect(screen, (0, 0, 0), y_rect)
        textsurface = score_font.render(
            "Score: " + str(env.score // REWARD * 10),
            True,
            (0, 0, 0),
        )
        screen.blit(
            textsurface, (SCREEN_WIDTH // 10, SCREEN_WIDTH + SCREEN_WIDTH // 20)
        )
