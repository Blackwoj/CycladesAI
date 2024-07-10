import math
import logging

import pygame
from pygame.event import Event

from ..DataCache import DataCache
from ..enums.GameState import GameState
from ..gui.common.Config import Config
from ..static.EventConfig import EventConfig
from .AbstractManager import AbstractManager
from typing import List
from .board_sub_managers.PrepareStageManger import PrepareStageManager
from .board_sub_managers.WarriorEntityManager import WarriorEntityManager
from .board_sub_managers.ShipEntityManager import ShipEntityManager
from .board_sub_managers.AppollonManager import AppollonManager
from ..dataclasses.BuildingDataClass import Building


class BoardManager(AbstractManager):

    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.StageManager = PrepareStageManager(self._screen, self.stage_type)
        self.entity_manager = {
            "warrior": WarriorEntityManager(self._screen, self.stage_type),
            "ship": ShipEntityManager(self._screen, self.stage_type),
            "income": AppollonManager(self._screen)
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
            self.read_cache_values()
            self.new_building_decider()
            self.save_cache_values()
        if event.type == EventConfig.CHECK_ATHENS:
            self.check_athens_card()

    def read_cache_values(self):
        self._islands_status = DataCache.get_value("islands_status")
        self._coins = DataCache.get_value("coins")
        super().read_cache_values()

    def save_cache_values(self):
        DataCache.set_value("islands_status", self._islands_status)
        DataCache.set_value("coins", self._coins)
        super().save_cache_values()

    @property
    def new_entity(self) -> dict[str, DataCache.AvailableSections]:
        return {
            "warrior": "new_warrior_location",
            "ship": "new_ship_location"  # rename to ship
        }

    def define_message(self, property: str, msg: str):
        moving_entity = DataCache.get_value(self.new_entity[property])
        if moving_entity[list(moving_entity.keys())[0]]["quantity"] == 1:
            self.entity_manager[property].valid_new_position()
            return
        DataCache.set_value(
            "message_board",
            {
                "property": property,
                "msg": msg
            }
        )

    def new_building_decider(self):
        building_location = DataCache.get_value("new_building")
        buildings_center = Config.boards.buildings_centers[self._num_of_players]
        buildings_status = DataCache.get_value("buildings_status")
        new_loc = ["IS1", "1"]
        closest_loc = 100000
        for island_id, island_data in self._islands_status.items():
            if island_data.owner == self._act_player:
                for i in range(len(buildings_center[island_id]["small"])):
                    if not island_data.small_building[str(i + 1)]:
                        temp_loc = self.calc_len(building_location, buildings_center[island_id]["small"][i])
                        new_loc = [island_id, str(i + 1)] if temp_loc < closest_loc else new_loc
                        closest_loc = temp_loc if temp_loc < closest_loc else closest_loc
        if closest_loc < 50 and self._coins[self._act_player] >= 2:
            self._coins[self._act_player] -= 2
            temp_id = self.generate_unique_id()
            buildings_status[temp_id] = Building(
                self._act_hero,
                buildings_center[new_loc[0]]["small"][int(new_loc[1]) - 1]
            )
            self._islands_status[new_loc[0]].small_building[new_loc[1]] = self._act_hero
            DataCache.set_value("buildings_status", buildings_status)
        else:
            DataCache.set_value("reset_building", True)

    def calc_len(self, dest_loc: List[int], point_loc: List[int]):
        return math.sqrt(
            (dest_loc[0] - point_loc[0])**2 + (dest_loc[1] - point_loc[1])**2
        )

    def check_athens_card(self):
        athens_cards = DataCache.get_value("philosophers")
        for player, quantity in athens_cards:
            if quantity >= 4:
                athens_cards[player] -= 4
            # self.pass
                pass

    def check_buildings_to_metro(self):
        pass
