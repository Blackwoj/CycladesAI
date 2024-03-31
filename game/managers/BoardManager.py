import pygame
from pygame.event import Event
from .AbstractManager import AbstractManager
from enum import Enum
from ..enums.GameState import GameState
from ..DataCache import DataCache
from ..gui.common.Config import Config
import time
import random
from ..static.EventConfig import EventConfig
import math


class BoardManager(AbstractManager):

    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)

    @property
    def stage_type(self) -> Enum:
        return GameState.BOARD

    def handle_events(self, event: Event):
        self.read_cache_values()
        if self._act_stage != self.stage_type:
            return
        if not self._water_status and not self._islands_status:
            self.setup_board_first_stage()
        if event.type is EventConfig.UPDATE_WARRIOR_POS:
            self.valid_warrior_pos()
        # if self.
        self.save_cache_values()

    def read_cache_values(self):
        self._water_status = DataCache.get_value("water_status")
        self._islands_status = DataCache.get_value("islands_status")
        self._warriors_status = DataCache.get_value("warriors_status")
        self._coins = DataCache.get_value("coins")
        self._heros = DataCache.get_value("hero_players")
        super().read_cache_values()

    def save_cache_values(self):
        DataCache.set_value("water_status", self._water_status)
        DataCache.set_value("islands_status", self._islands_status)
        DataCache.set_value("warriors_status", self._warriors_status)
        DataCache.set_value("coins", self._coins)
        DataCache.set_value("hero_players", self._heros)
        super().save_cache_values()

    def setup_board_first_stage(self):
        _water_config = Config.boards.water_config
        for circle, base_config in _water_config[str(DataCache.get_value("num_of_players"))].items():
            if base_config["owner"]:
                _player, _num_of_entities = next(iter(base_config["owner"].items()))
                self._water_status[circle] = {
                    "owner": _player,
                    "num_of_entities": _num_of_entities,
                    "income": base_config["base_income"]
                }
        _islands_config = Config.boards.islands_config
        for island, base_config in _islands_config[str(DataCache.get_value("num_of_players"))].items():
            if base_config["owner"]:
                _player, _num_of_entities = next(iter(base_config["owner"].items()))
                self._islands_status[island] = {
                    "owner": _player,
                    "num_of_entities": _num_of_entities,
                    "base_income": base_config["base_income"],
                    "income": 0,
                    "building": {
                        "small": {
                            key: "" for key in base_config["buildings"]["small"]
                        },
                        "big": False
                    }
                }
                self._warriors_status[self.generate_unique_id()] = {
                    "owner": _player,
                    "num_of_entities": _num_of_entities,
                    "island": island
                }

    def generate_unique_id(self) -> int:
        current_time_microseconds = int(time.time() * 1000000) + random.randint(-1000, 1000)
        return current_time_microseconds

    def valid_warrior_pos(self):
        distance = 1300
        new_island = ""
        for _id, location in DataCache.get_value("new_warrior_location").items():
            for island_id, island_location in Config.boards.islands_config.items():
                temp_distance = math.sqrt(
                    (location[0] - location[-1])**2 + (location[1] - island_location[1])**2
                )
                new_island = island_id if temp_distance < distance else new_island
                distance = temp_distance if temp_distance < distance else distance
        