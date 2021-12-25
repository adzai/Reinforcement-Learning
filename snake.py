import random
from copy import deepcopy
from enum import Enum

square_type = Enum("square_type", "empty snake food")

STRAIGHT = 0
UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3


class GameOver(Exception):
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
        self.observation_arr = None
        self.actions = [STRAIGHT, LEFT, RIGHT]
        self.grid_size = grid_size
        self.grid = [
            [square_type.empty for _ in range(self.grid_size)]
            for _ in range(self.grid_size)
        ]
        self.snake = self.spawn_snake()
        self.food = None
        self.score = 0
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
            print(snake.body)
            print(self.snake.body)
            snake.change_direction(action)
            new_y, new_x = self.get_new_coords(head_y, head_x, snake)
            snake = self.update_snake(
                Coordinates(new_x, new_y), snake, update_grid=False
            )
            print("After", snake.body, "direction", snake.direction)
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
        self.snake = self.update_snake(new_head, self.snake)
        if self.is_game_over(new_y, new_x):
            raise GameOver("Hit wall")
        if self.snake.ate_itself():
            raise GameOver("Ate itself")
        if new_head == self.food:
            snake.eat_food()
            self.score += 10
            self.food = None
        if self.food is None:
            self.spawn_food()
        self.observation()
        print("Danger:", self.get_danger())
        print(
            f"Observation dict: {self.observation_dict}\nObservation arr: {self.observation_arr}"
        )

    def observation(self):
        self.observation_dict = {
            "up": False,
            "right": False,
            "down": False,
            "left": False,
        }
        self.observation_arr = [0, 0, 0, 0]
        head = self.snake.body[0]
        if self.food is not None:
            if head.x > self.food.x:
                self.observation_dict["left"] = True
                self.observation_arr[LEFT] = 1
                self.observation_arr[RIGHT] = 0
                self.observation_dict["right"] = False
            if head.x < self.food.x:
                self.observation_dict["left"] = False
                self.observation_arr[LEFT] = 0
                self.observation_arr[RIGHT] = 1
                self.observation_dict["right"] = True
            if head.y < self.food.y:
                self.observation_dict["down"] = True
                self.observation_arr[DOWN] = 1
                self.observation_arr[UP] = 0
                self.observation_dict["up"] = False
            if head.y > self.food.y:
                self.observation_dict["up"] = True
                self.observation_arr[UP] = 1
                self.observation_arr[DOWN] = 0
                self.observation_dict["down"] = False

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


env = Environment(9)
snake = env.snake
env.print_board()
while True:
    print(env.actions)
    inp = input()
    if len(inp) > 1:
        inp = inp[0]
    if inp == "":
        inp = STRAIGHT
    elif inp == "a":
        inp = LEFT
    elif inp == "d":
        inp = RIGHT
    snake.change_direction(inp)
    env.move_snake()
    env.print_board()
