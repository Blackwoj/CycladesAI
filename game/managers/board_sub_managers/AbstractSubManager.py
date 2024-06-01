from abc import abstractmethod

import pygame

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
        return super().read_cache_values()

    @abstractmethod
    def save_cache_values(self):
        return super().save_cache_values()
