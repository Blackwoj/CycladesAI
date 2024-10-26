import logging
from typing import Any

import pygame
from pygame.event import Event

from ..DataCache import DataCache
from ..enums.GameState import GameState
from ..static.EventConfig import EventConfig
from .AbstractManager import AbstractManager
from .board_sub_managers.AppollonManager import AppollonManager
from .board_sub_managers.BuildingsEntityManager import BuildingsEntityManager
from .board_sub_managers.PrepareStageManger import PrepareStageManager
from .board_sub_managers.ShipEntityManager import ShipEntityManager
from .board_sub_managers.WarriorEntityManager import WarriorEntityManager


class BoardManager(AbstractManager):

    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.StageManager = PrepareStageManager(self._screen, self.stage_type)
        self.entity_manager = {
            "warrior": WarriorEntityManager(self._screen, self.stage_type),
            "ship": ShipEntityManager(self._screen, self.stage_type),
            "income": AppollonManager(self._screen),
            "building": BuildingsEntityManager(self._screen, self.stage_type)
        }
        self.StageManager.setup_board_first_stage()
        self.read_cache_values()

    @property
    def stage_type(self) -> GameState:
        return GameState.BOARD

    def handle_events(self, event: Event):
        self.read_cache_values()
        if self._act_stage != self.stage_type:
            return
        if DataCache.get_value("play_order") and not self._act_player:
            self.StageManager.define_player_hero()
            self.read_cache_values()
        if not DataCache.get_value("play_order") and not self._act_player:
            logging.info("Rodund end, calcualtin income and reset heros roll!")
            self.StageManager.end_stage()
        if event.type == EventConfig.UPDATE_WARRIOR_POS:
            self.entity_manager["warrior"].valid_new_position()
        if event.type == EventConfig.UPDATE_SHIP_POS:
            self.entity_manager["ship"].valid_new_position()
        if event.type == EventConfig.UPDATE_INCOME_POS:
            self.entity_manager["income"].valid_new_position()
        if event.type == EventConfig.SHOW_MULTIPLY_OPTIONS_WAR:
            self.read_cache_values()
            self.define_message("warrior", "Select how many soldiers you want to move")
            self.save_cache_values()
        if event.type == EventConfig.SHOW_MULTIPLY_OPTIONS_SHIP:
            self.read_cache_values()
            self.define_message("ship", "Select how many ship you want to move")
            self.save_cache_values()
        if event.type == EventConfig.NEW_BUILDING:
            self.entity_manager["building"].new_building_decider()
            self.save_cache_values()
        if event.type == EventConfig.CHECK_ATHENS:
            self.check_athens_card()
        if self.entity_manager["building"].check_if_metro():
            DataCache.set_value("metro_building_build", True)

    def read_cache_values(self):
        self._fields_status = DataCache.get_value("fields_status")
        self._coins = DataCache.get_value("coins")
        super().read_cache_values()

    def save_cache_values(self):
        DataCache.set_value("fields_status", self._fields_status)
        DataCache.set_value("coins", self._coins)
        super().save_cache_values()

    @property
    def new_entity(self) -> dict[str, DataCache.AvailableSections]:
        return {
            "warrior": "new_warrior_location",
            "ship": "new_ship_location"
        }

    def define_message(self, property: str, msg: str):
        moving_entity: dict[str, Any] = DataCache.get_value(self.new_entity[property])
        if moving_entity["quantity"] == 1:
            self.entity_manager[property].valid_new_position()
            return
        DataCache.set_value(
            "message_board",
            {
                "property": property,
                "msg": msg
            }
        )

    def check_athens_card(self):
        athens_cards = DataCache.get_value("philosophers")
        for player, quantity in athens_cards.items():
            if quantity >= 4:
                DataCache.set_value("metro_building_philo", True)
                athens_cards[player] -= 4
                pass
