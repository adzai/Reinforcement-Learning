from itertools import product
import random
from coordinates import Coordinates
from snake import Snake
from constants import STRAIGHT, LEFT, RIGHT, UP, DOWN, SQUARE_TYPE, COST, REWARD


class Environment:
    def __init__(self, grid_size, depth):
        self.depth = depth
        self.observation_dict = None
        self.state_size = 20 if depth else 11
        self.observation_arr = tuple([0]) * self.state_size
        self.observation_space = {
            arr: i for i, arr in enumerate(product([0, 1], repeat=self.state_size))
        }
        self.observation_space_len = len(self.observation_space.keys())
        self.action_space = [STRAIGHT, LEFT, RIGHT]
        self.action_space_len = len(self.action_space)
        self.grid_size = grid_size
        self.grid = [
            [SQUARE_TYPE.empty for _ in range(self.grid_size)]
            for _ in range(self.grid_size)
        ]
        self.snake = self.spawn_snake()
        self.food = None
        self.score = 0
        self.is_over = False
        self.spawn_food()

    def reset(self):
        self.observation_arr = tuple([0]) * self.state_size
        self.grid = [
            [SQUARE_TYPE.empty for _ in range(self.grid_size)]
            for _ in range(self.grid_size)
        ]
        self.snake = self.spawn_snake()
        self.food = None
        self.score = 0
        self.is_over = False
        self.spawn_food()
        return self.observation_space[self.observation_arr]

    def get_random_action(self):
        return random.choice(self.action_space)

    def spawn_snake(self):
        center = self.grid_size // 2
        y = center if center % 2 == 1 else center - 1
        snake_body = [Coordinates(x, y) for x in range(center - 1, center + 2)]
        for part in snake_body:
            self.grid[part.y][part.x] = SQUARE_TYPE.snake
        return Snake(snake_body)

    def spawn_food(self):
        available_coords = []
        for y, row in enumerate(self.grid):
            for x, _ in enumerate(row):
                if self.grid[y][x] == SQUARE_TYPE.empty:
                    available_coords.append(Coordinates(x, y))
        if len(available_coords) == 0:
            raise Won("You win!")
        chosen_coords = random.choice(available_coords)
        self.food = chosen_coords
        self.grid[chosen_coords.y][chosen_coords.x] = SQUARE_TYPE.food

    def is_game_over(self, new_y, new_x):
        return (
            new_y < 0 or new_y >= self.grid_size or new_x < 0 or new_x >= self.grid_size
        )

    def get_danger(self, snake, depth=False):
        head_y, head_x = (snake.body[0].y, snake.body[0].x)
        danger_arr = []
        for action in self.action_space:
            snake = Snake(self.snake.body)
            snake.change_direction(action)
            new_y, new_x = self.get_new_coords(head_y, head_x, snake)
            snake = self.update_snake(
                Coordinates(new_x, new_y), snake, update_grid=False
            )
            if self.is_game_over(new_y, new_x) or snake.ate_itself():
                danger_arr.append(1)
            else:
                danger_arr.append(0)
            if depth:
                danger_arr += self.get_danger(snake)
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
            self.grid[old_tail.y][old_tail.x] = SQUARE_TYPE.empty
        if update_grid:
            self.grid[new_head.y][new_head.x] = SQUARE_TYPE.snake
        return snake

    def move_snake(self):
        new_y, new_x = self.get_new_coords(
            self.snake.body[0].y, self.snake.body[0].x, self.snake
        )
        new_head = Coordinates(new_x, new_y)
        if self.is_game_over(new_y, new_x):
            self.is_over = True
            return
        if self.snake.ate_itself():
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
        danger_arr = self.get_danger(self.snake, self.depth)
        directions_arr = list(map(lambda x: int(x == self.snake.direction), range(4)))
        self.observation_arr = tuple(danger_arr + directions_arr + food_arr)

    def step(self, action):
        current_score = self.score
        self.snake.change_direction(action)
        try:
            self.move_snake()
        except Won:
            return None, REWARD, True
        reward = COST if self.is_over else self.score - current_score
        return self.observation_space[self.observation_arr], reward, self.is_over

    def print_board(self):
        head = self.snake.body[0]
        print(f"Score: {self.score}, Snake length: {self.snake.length}")
        for y, row in enumerate(self.grid):
            for x, _ in enumerate(row):
                if head.y == y and head.x == x:
                    print("O", end="")
                elif self.grid[y][x] == SQUARE_TYPE.snake:
                    print("=", end="")
                elif self.grid[y][x] == SQUARE_TYPE.food:
                    print("X", end="")
                else:
                    print("_", end="")
            print()
        print()


class GameOver(Exception):
    pass


class Won(Exception):
    pass
