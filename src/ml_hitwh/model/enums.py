from enum import Enum


class PlayerAndWind(int, Enum):
    four_men_east = 0
    four_men_south = 1


class GameState(int, Enum):
    uncompleted = 0
    completed = 1
    invalid_total_point = 2


class SeasonState(int, Enum):
    initial = 0
    running = 1
    finished = 2


class UserSeasonPointChangeType(Enum):
    game = 0
    manually = 1
