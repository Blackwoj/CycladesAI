from enum import Enum


class GameState(Enum):
    START = 1
    BOARD = 2
    ROLL = 3
    PAUSE = 4
    GAME_OVER = 5
