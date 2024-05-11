import math

import pygame
from pygame.event import Event

from ..DataCache import DataCache
from ..enums.GameState import GameState
from ..graph import Graph
from ..gui.common.Config import Config
from ..static.EventConfig import EventConfig
from .AbstractManager import AbstractManager
from typing import List
import logging
from .board_sub_managers.PrepareStageManger import PrepareStageManager


class BoardManager(AbstractManager):

    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.graph_warrior = Graph()
        self.StageManager = PrepareStageManager(self._screen, self.stage_type)
        self.StageManager.setup_board_first_stage()
        self.fill_graph()
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
        if event.type == EventConfig.UPDATE_WARRIOR_POS:
            self.valid_new_position("warrior")
        if event.type == EventConfig.UPDATE_SHIP_POS:
            self.valid_new_position("ship")
        if event.type == EventConfig.SHOW_MULTIPLY_OPTIONS_WAR:
            self.define_message("warrior", "Select how many soldiers you want to move")
        if event.type == EventConfig.SHOW_MULTIPLY_OPTIONS_SHIP:
            self.define_message("ship", "Select how many ship you want to move")
        if event.type == EventConfig.NEW_BUILDING:
            self.new_building_decider()
        self.save_cache_values()

    def read_cache_values(self):
        self._ships_status = DataCache.get_value("ship_status")
        self._water_status = DataCache.get_value("water_status")
        self._islands_status = DataCache.get_value("islands_status")
        self._warriors_status = DataCache.get_value("warriors_status")
        self._coins = DataCache.get_value("coins")
        self._heros = DataCache.get_value("hero_players")
        self.entity_to_delete = DataCache.get_value("entity_delete")
        super().read_cache_values()

    def save_cache_values(self):
        DataCache.set_value("ship_status", self._ships_status)
        DataCache.set_value("islands_status", self._islands_status)
        DataCache.set_value("warriors_status", self._warriors_status)
        DataCache.set_value("water_status", self._water_status)
        DataCache.set_value("coins", self._coins)
        DataCache.set_value("hero_players", self._heros)
        DataCache.set_value("entity_delete", self.entity_to_delete)
        super().save_cache_values()

    @property
    def filed_config(self):
        return {
            "warrior": Config.boards.islands_config,
            "ship": Config.boards.water_config
        }

    @property
    def new_entity(self) -> dict[str, DataCache.AvailableSections]:
        return {
            "warrior": "new_warrior_location",
            "ship": "new_ship_location"  # rename to ship
        }

    @property
    def entity_status(self):
        return {
            "warrior": self._warriors_status,
            "ship": self._ships_status
        }

    @property
    def entities_points(self):
        return {
            "warrior": Config.boards.warriors_points[self._num_of_players],
            "ship": Config.boards.circles_centers[self._num_of_players]
        }

    def valid_new_position(self, type: str):
        available_posejdon_jumps = DataCache.get_value("posejdon_move")
        distance = 1300000
        new_place = ""
        centers_loc = Config.boards.circles_centers[self._num_of_players]
        moving_entity = DataCache.get_value(self.new_entity[type])
        moving_entity_id = ""
        for _id, location in moving_entity.items():
            moving_entity_id = _id
            for field_id, field_config in self.filed_config[type][self._num_of_players].items():
                filed_to_check = []
                if "location" in field_config.keys():
                    filed_to_check = field_config["location"]
                else:
                    filed_to_check.append(field_id)
                for center in filed_to_check:
                    temp_distance = self.calc_len(location["location"], centers_loc[center])
                    new_place = field_id if temp_distance < distance else new_place
                    distance = temp_distance if temp_distance < distance else distance
        if new_place:
            self.update_graph_colors()
            entity_status = self.entity_status[type]
            entity_map_points = self.entities_points[type]
            if self._coins[entity_status[moving_entity_id]["owner"]] >= 1:
                if type == "warrior" and self.graph_warrior.has_connection(
                    entity_status[moving_entity_id]["field"],
                    new_place,
                    entity_status[moving_entity_id]["owner"]
                ):
                    self._coins[entity_status[moving_entity_id]["owner"]] -= 1
                    self.move_entity("warrior", moving_entity, moving_entity_id, new_place, entity_map_points, entity_status)
                elif (
                    type == "ship"
                    and (
                        available_posejdon_jumps > 0
                        or self._coins[entity_status[moving_entity_id]["owner"]]
                    )
                    and (
                        self._ships_status[moving_entity_id]["field"] in self.filed_config[type][self._num_of_players][new_place]["neighbors"]
                    )
                ):
                    if available_posejdon_jumps == 0:
                        self._coins[entity_status[moving_entity_id]["owner"]] -= 1
                        DataCache.set_value("posejdon_move", 2)
                    else:
                        DataCache.set_value("posejdon_move", available_posejdon_jumps - 1)
                    self.move_entity("ship", moving_entity, moving_entity_id, new_place, entity_map_points, entity_status)
                else:
                    update_entity = DataCache.get_value("entity_update")
                    update_entity[moving_entity_id] = {
                        "location": entity_map_points[entity_status[moving_entity_id]["field"]],
                        "num_of_entities": entity_status[moving_entity_id]["num_of_entities"]
                    }
                    DataCache.set_value("entity_update", update_entity)
                    logging.info("No enough money to move %s!", type)
            self.clear_message()

    @property
    def field_status(self):
        return {
            "warrior": self._islands_status,
            "ship": self._water_status
        }

    def move_entity(self, type, moving_entity, moving_entity_id, new_place, entity_map_points, entity_status):
        entities_stats = self.entity_status[type]
        fields_stats = self.field_status[type]
        entity_split = self.split_entity_number(
            moving_entity[moving_entity_id],
            entities_stats[moving_entity_id]
        )
        self.send_update_warrior(
            type,
            moving_entity_id,
            entity_map_points,
            entity_split[1],
            entities_stats[moving_entity_id]["field"]
        )
        if type == "ship" and entity_split[1] == 0:
            self.delete_entity(moving_entity_id)
            fields_stats[entities_stats[moving_entity_id]["field"]]["owner"] = "None"
            fields_stats[entities_stats[moving_entity_id]["field"]]["num_of_entity"] = 0
        else:
            fields_stats[
                entities_stats[moving_entity_id]["field"]
            ]["num_of_entities"] = entity_split[1]
        if fields_stats[new_place]["owner"] == "None":
            entities_stats[self.generate_unique_id()] = {
                "owner": entity_status[moving_entity_id]["owner"],
                "num_of_entities": entity_split[0],
                "field": new_place
            }
            fields_stats[new_place]["owner"] = entity_status[moving_entity_id]["owner"]

        elif fields_stats[new_place]["owner"] == entity_status[moving_entity_id]["owner"]:
            for id, entity_stat in entities_stats.items():
                if entity_stat["field"] == new_place:

                    self.send_update_warrior(
                        type,
                        id,
                        entity_map_points,
                        entity_stat["num_of_entities"] + entity_split[0],
                        new_place
                    )
        else:
            attacker_entity_count = entity_split[0]
            war_diff = attacker_entity_count - fields_stats[new_place]["num_of_entities"]
            defensive_entity_id = ""
            for id, entity_stat in entities_stats.items():
                if entity_stat["field"] == new_place:
                    defensive_entity_id = id
            if war_diff > 0:
                entities_stats[self.generate_unique_id()] = {
                    "owner": entity_status[moving_entity_id]["owner"],
                    "num_of_entities": war_diff,
                    "field": new_place
                }
                fields_stats[new_place]["owner"] = entity_status[moving_entity_id]["owner"]
                self.delete_entity(defensive_entity_id)
                pass
            elif war_diff <= 0:
                war_diff = abs(war_diff)
                self.send_update_warrior(
                    type,
                    defensive_entity_id,
                    entity_map_points,
                    war_diff,
                    new_place
                )
            fields_stats[new_place]["num_of_entities"] = war_diff

    def send_update_warrior(self, type, entity_id, map_points, entity_num_value, new_place):
        update_entity = DataCache.get_value("entity_update")
        update_entity[entity_id] = {
            "location": map_points[new_place],
            "num_of_entities": entity_num_value
        }
        self.entity_status[type][entity_id]["field"] = new_place
        self.entity_status[type][entity_id]["num_of_entities"] = entity_num_value
        self.field_status[type][new_place]["num_of_entities"] = entity_num_value
        DataCache.set_value("entity_update", update_entity)

    @staticmethod
    def split_entity_number(moving_entity, base_entity_stat):
        return [
            moving_entity["num_of_entities"],
            base_entity_stat["num_of_entities"] - moving_entity["num_of_entities"]
        ]

    def delete_entity(self, entity_id):
        self.entity_to_delete.append(entity_id)

    def fill_graph(self):
        _water_config = Config.boards.water_config
        for ver in _water_config[str(DataCache.get_value("num_of_players"))].keys():
            self.graph_warrior.add_vertex(ver, "None")
        _island_vertex = Config.boards.islands_config
        for ver in _island_vertex[str(DataCache.get_value("num_of_players"))].keys():
            self.graph_warrior.add_vertex(ver, "None")
        for ver, ver_config in _water_config[str(DataCache.get_value("num_of_players"))].items():
            for neighbors in ver_config["neighbors"]:
                self.graph_warrior.add_edge(ver, neighbors)
            for neighbors in ver_config["neighbors_island"]:
                self.graph_warrior.add_edge(ver, neighbors)

    def update_graph_colors(self):
        print(self._islands_status)
        island_colors = {key: values["owner"] for key, values in self._islands_status.items()}
        water_colors = {values["field"]: values["owner"] for _, values in self._ships_status.items()}
        fields_colors = island_colors | water_colors
        if self.graph_warrior.colors != fields_colors:
            for key, color in fields_colors.items():
                self.graph_warrior.set_vertex_color(key, color)

    def define_message(self, property: str, msg: str):
        moving_entity = DataCache.get_value(self.new_entity[property])
        if moving_entity[list(moving_entity.keys())[0]]["num_of_entities"] == 1:
            self.valid_new_position(property)
            return
        DataCache.set_value(
            "message_board",
            {
                "property": property,
                "msg": msg
            }
        )

    def clear_message(self):
        DataCache.set_value("message_board", "")

    def new_building_decider(self):
        building_location = DataCache.get_value("new_building")
        buildings_center = Config.boards.buildings_centers[self._num_of_players]
        buildings_status = DataCache.get_value("buildings_status")
        new_loc = ["IS1", "1"]
        closest_loc = 100000
        for island_id, island_data in self._islands_status.items():
            if island_data["owner"] == self._act_player:
                for i in range(len(buildings_center[island_id]["small"])):
                    if not island_data["building"]["small"][str(i + 1)]:
                        temp_loc = self.calc_len(building_location, buildings_center[island_id]["small"][i])
                        new_loc = [island_id, str(i + 1)] if temp_loc < closest_loc else new_loc
                        closest_loc = temp_loc if temp_loc < closest_loc else closest_loc
        if closest_loc < 50 and self._coins[self._act_player] >= 2:
            self._coins[self._act_player] -= 2
            temp_id = self.generate_unique_id()
            buildings_status[temp_id] = {
                "hero": self._act_hero,
                "loc": buildings_center[new_loc[0]]["small"][int(new_loc[1]) - 1]
            }
            self._islands_status[new_loc[0]]["building"]["small"][new_loc[1]] = self._act_hero
            DataCache.set_value("buildings_status", buildings_status)
        else:
            DataCache.set_value("reset_building", True)

    def calc_len(self, dest_loc: List[int], point_loc: List[int]):
        return math.sqrt(
            (dest_loc[0] - point_loc[0])**2 + (dest_loc[1] - point_loc[1])**2
        )
