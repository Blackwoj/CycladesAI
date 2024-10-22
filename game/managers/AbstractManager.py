import random
import time
from abc import ABC, abstractmethod

import pygame

from ..DataCache import DataCache


class AbstractManager(ABC):

    def __init__(self, screen: pygame.Surface):
        self._screen = screen
        self._act_hero = ""

    @abstractmethod
    def stage_type(self):
        raise NotImplementedError

    @abstractmethod
    def handle_events(self, event: pygame.event.Event):
        raise NotImplementedError

    @abstractmethod
    def read_cache_values(self):
        self._act_stage = DataCache.get_value("act_stage")
        self._act_hero = DataCache.get_value("act_hero")
        self._act_player = DataCache.get_value("act_player")
        self._num_of_players = str(DataCache.get_value("num_of_players"))

    @abstractmethod
    def save_cache_values(self):
        DataCache.set_value("act_stage", self._act_stage)
        DataCache.set_value("act_player", self._act_player)
        DataCache.set_value("act_hero", self._act_hero)

    def generate_unique_id(self) -> int:
        randomize_int = random.randint(-1000, 1000)
        current_time_microseconds = int(time.time() * 1000000) + randomize_int
        if current_time_microseconds in [2, 0, -1, -2, -3, -4]:
            current_time_microseconds = self.generate_unique_id()
        return current_time_microseconds
