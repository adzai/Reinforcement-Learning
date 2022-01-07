import random
from copy import deepcopy
from enum import Enum
import argparse
import sys
import numpy as np
from itertools import product


square_type = Enum("square_type", "empty snake food")


STRAIGHT = 0
UP = 0
DOWN = 3
LEFT = 1
RIGHT = 2


parser = argparse.ArgumentParser(description="Snake Game RL")
parser.add_argument("-t", "--train", action="store_true", help="Training mode")
parser.add_argument("-p", "--play", action="store_true", help="AI playing mode")
parser.add_argument("-q", "--q_table", type=str, help="Path to .npy Q table")
parser.add_argument("--survival_reward", type=int, default=2, help="Survival reward")
parser.add_argument("--cost", type=int, default=-20, help="Cost for reaching game over")
parser.add_argument("--reward", type=int, default=150, help="Reward for eating food")
parser.add_argument(
    "--speed",
    type=int,
    default=100,
    help="Speed of updating the snake game played in pygame in milliseconds. Default: 100",
)
parser.add_argument(
    "-l",
    "--learning_rate",
    type=float,
    default=0.75,
    help="Learning rate used for training. Default: 0.75",
)
parser.add_argument(
    "-d",
    "--decay_rate",
    type=float,
    default=0.0004,
    help="Decay rate used for training. Default: 0.0004",
)
parser.add_argument(
    "--total_episodes",
    type=int,
    default=100_000,
    help="Number of total episodes that should be used for training. Default: 100000",
)
parser.add_argument(
    "-o",
    "--output",
    type=str,
    default="snake_q_table.npy",
    help="Path where .npy Q table will be saved. Default: snake_q_table.npy",
)
parser.add_argument(
    "--env_size",
    default=3,
    type=int,
    help="Environment size (e.g. --env_size 16 will create 16x16 env)."
    + " When --play is supplied, only 16x16 is used. Default: 3",
)
args = parser.parse_args()

SURVIVAL_REWARD = args.survival_reward
COST = args.cost
REWARD = args.reward

if not args.train and not args.play:
    print("Must specify mode: Use either --play or --train")
    sys.exit(1)


class GameOver(Exception):
    pass


class Won(Exception):
    pass


class Snake:
    def __init__(self, body_coords):
        self.direction = LEFT
        self.length = len(body_coords)
        self.body = body_coords
        self.food_idx = None

    def change_direction(self, direction):
        if direction == STRAIGHT:
            return
        elif self.direction == LEFT and direction == RIGHT:
            self.direction = UP
        elif self.direction == LEFT and direction == LEFT:
            self.direction = DOWN
        elif self.direction == RIGHT and direction == LEFT:
            self.direction = UP
        elif self.direction == RIGHT and direction == RIGHT:
            self.direction = DOWN
        elif self.direction == UP and direction == LEFT:
            self.direction = LEFT
        elif self.direction == UP and direction == RIGHT:
            self.direction = RIGHT
        elif self.direction == DOWN and direction == LEFT:
            self.direction = RIGHT
        elif self.direction == RIGHT and direction == RIGHT:
            self.direction = DOWN
        elif self.direction == DOWN and direction == RIGHT:
            self.direction = LEFT

    def eat_food(self):
        self.food_idx = 0

    def process_food(self):
        if self.food_idx is None:
            return
        self.food_idx += 1

    def add_tail(self, coords):
        self.length += 1
        self.body.append(coords)
        self.food_idx = None

    def ate_itself(self):
        head = self.body[0]
        for part in self.body[1:]:
            if head.x == part.x and head.y == part.y:
                return True
        return False


class Coordinates:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        return f"(X: {self.x}, Y: {self.y})"


class Environment:
    def __init__(self, grid_size):
        self.observation_dict = None
        self.state_size = 11
        self.observation_arr = tuple([0]) * self.state_size
        self.observation_space = {
            arr: i for i, arr in enumerate(product([0, 1], repeat=self.state_size))
        }
        self.observation_space_len = len(self.observation_space.keys())
        self.action_space = [STRAIGHT, LEFT, RIGHT]
        self.action_space_len = len(self.action_space)
        self.grid_size = grid_size
        self.grid = [
            [square_type.empty for _ in range(self.grid_size)]
            for _ in range(self.grid_size)
        ]
        self.snake = self.spawn_snake()
        self.food = None
        self.score = 0
        self.is_over = False
        self.spawn_food()

    def reset(self):
        self.__init__(self.grid_size)
        return self.observation_space[self.observation_arr]

    def get_random_action(self):
        return random.choice(self.action_space)

    def spawn_snake(self):
        center = self.grid_size // 2
        y = center if center % 2 == 1 else center - 1
        snake_body = [Coordinates(x, y) for x in range(center - 1, center + 2)]
        for part in snake_body:
            self.grid[part.y][part.x] = square_type.snake
        return Snake(snake_body)

    def spawn_food(self):
        available_coords = []
        for y, row in enumerate(self.grid):
            for x, _ in enumerate(row):
                if self.grid[y][x] == square_type.empty:
                    available_coords.append(Coordinates(x, y))
        if len(available_coords) == 0:
            raise Won("You win!")
        chosen_coords = random.choice(available_coords)
        self.food = chosen_coords
        self.grid[chosen_coords.y][chosen_coords.x] = square_type.food

    def is_game_over(self, new_y, new_x):
        return (
            new_y < 0 or new_y >= self.grid_size or new_x < 0 or new_x >= self.grid_size
        )

    def get_danger(self):
        head_y, head_x = (self.snake.body[0].y, self.snake.body[0].x)
        danger_arr = []
        for action in self.action_space:
            snake = deepcopy(self.snake)
            snake.change_direction(action)
            new_y, new_x = self.get_new_coords(head_y, head_x, snake)
            snake = self.update_snake(
                Coordinates(new_x, new_y), snake, update_grid=False
            )
            if self.is_game_over(new_y, new_x) or snake.ate_itself():
                danger_arr.append(1)
            else:
                danger_arr.append(0)
        return danger_arr

    def get_new_coords(self, y, x, snake):
        if snake.direction == UP:
            y = snake.body[0].y - 1
        elif snake.direction == DOWN:
            y = snake.body[0].y + 1
        elif snake.direction == LEFT:
            x = snake.body[0].x - 1
        elif snake.direction == RIGHT:
            x = snake.body[0].x + 1
        else:
            raise Exception(f"Wrong snake direction: {snake.direction}")
        return y, x

    def update_snake(self, new_head, snake, update_grid=True):
        old_tail = snake.body[-1]
        snake.process_food()
        snake.body = [new_head] + snake.body[:-1]
        if snake.food_idx == snake.length:
            snake.add_tail(old_tail)
        elif update_grid:
            self.grid[old_tail.y][old_tail.x] = square_type.empty
        if update_grid:
            self.grid[new_head.y][new_head.x] = square_type.snake
        return snake

    def move_snake(self):
        new_y, new_x = self.get_new_coords(
            self.snake.body[0].y, self.snake.body[0].x, self.snake
        )
        new_head = Coordinates(new_x, new_y)
        if self.is_game_over(new_y, new_x):
            # print("Hit wall")
            self.is_over = True
            return
        if self.snake.ate_itself():
            # print("Ate itself")
            self.is_over = True
            return
        self.snake = self.update_snake(new_head, self.snake)
        if new_head == self.food:
            self.snake.eat_food()
            self.score += REWARD
            self.food = None
        if self.food is None:
            self.spawn_food()
        self.observation()

    def observation(self):
        self.observation_dict = {
            "up": False,
            "right": False,
            "down": False,
            "left": False,
        }
        food_arr = [0, 0, 0, 0]
        head = self.snake.body[0]
        if self.food is not None:
            if head.x > self.food.x:
                self.observation_dict["left"] = True
                food_arr[LEFT] = 1
                food_arr[RIGHT] = 0
                self.observation_dict["right"] = False
            if head.x < self.food.x:
                self.observation_dict["left"] = False
                food_arr[LEFT] = 0
                food_arr[RIGHT] = 1
                self.observation_dict["right"] = True
            if head.y < self.food.y:
                self.observation_dict["down"] = True
                food_arr[DOWN] = 1
                food_arr[UP] = 0
                self.observation_dict["up"] = False
            if head.y > self.food.y:
                self.observation_dict["up"] = True
                food_arr[UP] = 1
                food_arr[DOWN] = 0
                self.observation_dict["down"] = False
        danger_arr = self.get_danger()
        directions_arr = list(map(lambda x: int(x == self.snake.direction), range(4)))
        self.observation_arr = tuple(danger_arr + directions_arr + food_arr)

    def step(self, action):
        current_score = self.score
        self.snake.change_direction(action)
        try:
            self.move_snake()
        except Won:
            return None, 1000, True
        reward = COST if self.is_over else self.score - current_score  # 2 for survival
        return self.observation_space[self.observation_arr], reward, self.is_over

    def print_board(self):
        head = self.snake.body[0]
        print(f"Score: {self.score}, Snake length: {self.snake.length}")
        for y, row in enumerate(self.grid):
            for x, _ in enumerate(row):
                if head.y == y and head.x == x:
                    print("O", end="")
                elif self.grid[y][x] == square_type.snake:
                    print("=", end="")
                elif self.grid[y][x] == square_type.food:
                    print("X", end="")
                else:
                    print("_", end="")
            print()
        print()

    def print_pygame(self):
        head = self.snake.body[0]
        for y, row in enumerate(self.grid):
            for x, _ in enumerate(row):
                if head.y == y and head.x == x:
                    rect = pygame.Rect(
                        head.x * width,
                        head.y * width,
                        width,
                        width,
                    )
                    pygame.draw.rect(screen, (200, 0, 0), rect)
                elif self.grid[y][x] == square_type.snake:
                    rect = pygame.Rect(
                        x * width + 10, y * width + 10, snake_width, snake_width
                    )
                    pygame.draw.rect(screen, (34, 139, 34), rect)
                elif self.grid[y][x] == square_type.food:
                    rect = pygame.Rect(
                        x * width + 10,
                        y * width + 10,
                        snake_width,
                        snake_width,
                    )
                    pygame.draw.rect(screen, (0, 0, 255), rect)

            pygame.draw.rect(screen, (0, 0, 0), line_rect)
            textsurface = score_font.render(
                "Score: " + str(env.score // REWARD * 10),
                True,
                (0, 0, 0),
            )
            screen.blit(
                textsurface, (SCREEN_WIDTH // 10, SCREEN_WIDTH + SCREEN_WIDTH // 20)
            )


# env = Environment(5)
# snake = env.snake
# env.print_board()
# while True:
#     print(env.actions)
#     inp = input()
#     if len(inp) > 1:
#         inp = inp[0]
#     if inp == "q":
#         break
#     elif inp == "":
#         inp = STRAIGHT
#     elif inp == "a":
#         inp = LEFT
#     elif inp == "d":
#         inp = RIGHT
#     _, _, done = env.step(inp)
#     if done:
#         print("Game over")
#         break
#     env.print_board()


def ai_play(qtable, env_size):
    env = Environment(env_size)
    state = env.reset()
    done = False
    while not done:
        action = np.argmax(qtable[state, :])
        new_state, _, done = env.step(action)
        state = new_state


if args.play:
    import pygame

    SCREEN_WIDTH = 720
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_WIDTH + SCREEN_WIDTH // 10))
    width = SCREEN_WIDTH // 16
    snake_width = 25
    x, y = 0, 0
    line_rect = pygame.Rect(0, SCREEN_WIDTH + 1, SCREEN_WIDTH + SCREEN_WIDTH // 10, 1)
    dir, size = (0, 0), 20
    MOVEEVENT = pygame.USEREVENT + 1
    t = args.speed
    pygame.time.set_timer(MOVEEVENT, t)

    pygame.init()
    pygame.font.init()
    score_font = pygame.font.SysFont("arial", 30)
    done = False
    inp = None
    env = Environment(16)
    state = env.observation_arr
    running = True
    if args.q_table is None:
        print(
            "Must provide --q_table argument with path to a q table saved as a numpy array."
        )
        sys.exit(2)
    try:
        q_table = np.load(args.q_table)
    except Exception as e:
        print(f"Couldn't load q table {args.q_table}: {e}")
        sys.exit(3)
    while running:
        keys = pygame.key.get_pressed()
        if not done:
            for e in pygame.event.get():
                if e.type == MOVEEVENT:  # is called every 't' milliseconds
                    action = np.argmax(q_table[state, :])
                    new_state, _, done = env.step(action)
                    state = new_state

        screen.fill((192, 192, 192))
        env.print_pygame()
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

else:
    import matplotlib.pyplot as plt

    env = Environment(args.env_size)
    total_episodes = args.total_episodes
    learning_rate = args.learning_rate
    gamma = 0.90
    epsilon = 1.0
    max_epsilon = 1.0
    min_epsilon = 0.01
    decay_rate = args.decay_rate
    explored_states = dict()
    q_table = np.zeros((env.observation_space_len, env.action_space_len))
    rewards = []
    aggr_ep_rewards = {"ep": [], "avg": [], "max": [], "moves": []}
    moves_per_episode = []
    for episode in range(1, total_episodes + 1):
        state = env.reset()
        step = 0
        done = False
        total_rewards = 0
        moves = 0
        while not done and moves != 100_000:
            exploit = random.uniform(0, 1)

            if exploit > epsilon:
                action = np.argmax(q_table[state, :])
            else:
                action = env.get_random_action()

            new_state, reward, done = env.step(action)
            moves += 1

            if not done:
                total_rewards += reward // REWARD * 10
                reward += SURVIVAL_REWARD

            explored_states[state] = 1
            q_table[state, action] = q_table[state, action] + learning_rate * (
                reward + gamma * np.max(q_table[new_state, :]) - q_table[state, action]
            )

            state = new_state

        moves_per_episode.append(moves)
        epsilon = min_epsilon + (max_epsilon - min_epsilon) * np.exp(
            -decay_rate * episode
        )
        if episode % 1000 == 0:
            aggr_ep_rewards["ep"].append(episode)
            aggr_ep_rewards["avg"].append(sum(rewards) / episode)
            aggr_ep_rewards["max"].append(max(rewards))
            aggr_ep_rewards["moves"].append(sum(moves_per_episode) / episode)
            print(
                f"{episode} ep, average score: {sum(rewards) / episode:.2f}, epsilon: {epsilon}, explored states: {len(explored_states.keys())}, max score: {max(rewards)}, average moves: {sum(moves_per_episode) / episode:.2f}"
            )
        rewards.append(total_rewards)

    print("Score over time: " + str(sum(rewards) / total_episodes))

    np.save(args.output, q_table)
    plt.plot(aggr_ep_rewards["ep"], aggr_ep_rewards["avg"], label="average rewards")
    plt.plot(aggr_ep_rewards["ep"], aggr_ep_rewards["max"], label="max rewards")
    plt.plot(aggr_ep_rewards["ep"], aggr_ep_rewards["moves"], label="min rewards")
    plt.legend(loc=4)
    qtable_save_location = args.output
    print(f"Q table saved to {qtable_save_location}")
    fig_save_location = qtable_save_location.split(".npy")[0] + "_fig.png"
    plt.savefig(fig_save_location)
    print(f"Plot saved to {fig_save_location}")
