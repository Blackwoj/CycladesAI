from abc import ABC, abstractmethod, abstractproperty
import pygame
from ..DataCache import DataCache


class AbstractManager(ABC):

    def __init__(self, screen: pygame.Surface):
        self._screen = screen

    @abstractproperty
    def stage_type(self):
        raise NotImplementedError

    @abstractmethod
    def handle_events(self, event: pygame.event.Event):
        raise NotImplementedError

    @abstractmethod
    def read_cache_values(self):
        self._act_stage = DataCache.get_value("act_stage")
        self._act_player = DataCache.get_value("act_player")
        self._num_of_players = str(DataCache.get_value("num_of_players"))

    @abstractmethod
    def save_cache_values(self):
        DataCache.set_value("act_stage", self._act_stage)
        DataCache.set_value("act_player", self._act_player)
