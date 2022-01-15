from constants import STRAIGHT, LEFT, RIGHT, UP, DOWN


class Snake:
    def __init__(self, body_coords):
        self.direction = LEFT
        self.length = len(body_coords)
        self.body = body_coords
        self.food_idx = None

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
