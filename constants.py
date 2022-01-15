from enum import Enum

STRAIGHT = 0
UP = 0
DOWN = 3
LEFT = 1
RIGHT = 2
COST = -300
REWARD = 150
SURVIVAL_REWARD = 0

SQUARE_TYPE = Enum("square_type", "empty snake food")
