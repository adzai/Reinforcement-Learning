import pygame
import random
from copy import deepcopy
from enum import Enum


from itertools import product

square_type = Enum("square_type", "empty snake food")
obs_space = {}
for i, arr in enumerate(product([0, 1], repeat=11)):
    obs_space[arr] = i


STRAIGHT = 0
UP = 0
DOWN = 3
LEFT = 1
RIGHT = 2

COST = -20
REWARD = 50

screen = pygame.display.set_mode((720, 720))
player = pygame.Rect(300, 300, 20, 20)
width = 720 / 16
snake_width = 25
x, y = 0, 0
rects = []
for _ in range(16):
    for row in range(16):
        rects.append(pygame.Rect(x, y, width, width))
        x += width
    x = 0
    y += width

dir, size = (0, 0), 20
MOVEEVENT, t = pygame.USEREVENT + 1, 100
pygame.time.set_timer(MOVEEVENT, t)
red, green, blue = 255, 255, 255

pygame.init()
done = False
inp = None


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
        self.observation_arr = tuple([0]) * 11
        self.actions = [STRAIGHT, LEFT, RIGHT]
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
        for action in self.actions:
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
        reward = COST if self.is_over else self.score - current_score
        obs = obs_space[self.observation_arr]
        return obs, reward, self.is_over

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
        # print(f"Score: {self.score}, Snake length: {self.snake.length}")
        for y, row in enumerate(self.grid):
            for x, _ in enumerate(row):
                if head.y == y and head.x == x:
                    rect = pygame.Rect(
                        head.x * width,
                        head.y * width,
                        width,
                        width,
                    )
                    pygame.draw.rect(screen, (255, 0, 0), rect)
                elif self.grid[y][x] == square_type.snake:
                    rect = pygame.Rect(
                        x * width + 10, y * width + 10, snake_width, snake_width
                    )
                    pygame.draw.rect(screen, (0, 255, 0), rect)
                elif self.grid[y][x] == square_type.food:
                    rect = pygame.Rect(
                        x * width + 10,
                        y * width + 10,
                        snake_width,
                        snake_width,
                    )
                    pygame.draw.rect(screen, (0, 0, 255), rect)


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

import numpy as np


rewards = []
inputs = []

total_episodes = 50_000
learning_rate = 0.75
gamma = 0.90
epsilon = 1.0
max_epsilon = 1.0
min_epsilon = 0.01
decay_rate = 0.0004

q_table = np.zeros((len(obs_space.keys()), 3))

explored_states = dict()

import time


def ai_play(qtable, env_size):
    env = Environment(env_size)
    state = obs_space[env.observation_arr]
    done = False
    while not done:
        action = np.argmax(qtable[state, :])
        new_state, _, done = env.step(action)
        state = new_state


q_table = np.load("q_table3.npy")
# ai_play(q_table, 16)
# print(inputs)

env = Environment(16)
state = env.observation_arr
while not done:
    keys = pygame.key.get_pressed()
    # if pygame.event.get(pygame.QUIT):
    #     break
    for e in pygame.event.get():
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_d:
                inputs.append(RIGHT)
            elif e.key == pygame.K_a:
                inputs.append(LEFT)
        elif e.type == MOVEEVENT:  # is called every 't' milliseconds
            action = np.argmax(q_table[state, :])
            new_state, _, done = env.step(action)
            state = new_state

    screen.fill((211, 211, 211))
    env.print_pygame()
    # for t in trail:
    #     pygame.draw.rect(screen, (255, 0, 0), t)
    # rect = pygame.Rect(head.x * width, head.y * width, width, width)
    # pygame.draw.rect(screen, (255, 0, 0), rect)
    pygame.display.flip()

# for episode in range(total_episodes):
#     env = Environment(3)
#     state = obs_space[env.observation_arr]
#     step = 0
#     done = False
#     total_rewards = 0

#     while not done:
#         exploit = random.uniform(0, 1)

#         if exploit > epsilon:
#             action = np.argmax(q_table[state, :])
#         else:
#             action = random.randint(0, 2)

#         if episode == (total_episodes - 1):
#             inputs.append(action)
#         new_state, reward, done = env.step(action)

#         if reward > 0:
#             total_rewards += 10
#         else:
#             reward += 2

#         explored_states[state] = 1
#         q_table[state, action] = q_table[state, action] + learning_rate * (
#             reward + gamma * np.max(q_table[new_state, :]) - q_table[state, action]
#         )

#         state = new_state

#     epsilon = min_epsilon + (max_epsilon - min_epsilon) * np.exp(-decay_rate * episode)
#     # print("Epsilon:", epsilon)
#     # print("Reward:", total_rewards)
#     if (episode + 1) % 1000 == 0:
#         print(
#             f"{episode} average: {str(sum(rewards) / episode)}, epsilon: {epsilon}, explored states: {len(explored_states.keys())}, max reward: {max(rewards)}"
#         )
#     # if (episode + 1) % 10000 == 0:
#     #     ai_play(qtable)
#     rewards.append(total_rewards)


# print("Score over time: " + str(sum(rewards) / total_episodes))
# import sys

# print(q_table)
# np.save("q_table3.npy", q_table)
