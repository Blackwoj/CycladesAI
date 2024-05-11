from abc import abstractmethod

import pygame

from ...DataCache import DataCache
from ..AbstractManager import AbstractManager
from ...enums.GameState import GameState


class AbstractSubManager(AbstractManager):

    def __init__(self, screen: pygame.Surface, stage: GameState):
        super().__init__(screen)
        self.stage = stage

    @property
    def stage_type(self):
        self.stage

    @abstractmethod
    def read_cache_values(self):
        self._act_stage = DataCache.get_value("act_stage")
        self._act_player = DataCache.get_value("act_player")
        self._num_of_players = str(DataCache.get_value("num_of_players"))

    @abstractmethod
    def save_cache_values(self):
        DataCache.set_value("act_stage", self._act_stage)
        DataCache.set_value("act_player", self._act_player)
        DataCache.set_value("act_hero", self._act_hero)
