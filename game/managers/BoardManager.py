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
from ..graph import Graph


class BoardManager(AbstractManager):

    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.Graph = Graph()
        self.fill_graph()

    @property
    def stage_type(self) -> Enum:
        return GameState.BOARD

    def handle_events(self, event: Event):
        self.read_cache_values()
        if self._act_stage != self.stage_type:
            return
        # if not DataCache.get_value("board_row"):
        if not self._ships_status and not self._islands_status:
            self.setup_board_first_stage()
        if event.type == EventConfig.UPDATE_WARRIOR_POS:
            self.valid_new_position("warrior")
            # self.valid_warrior_pos()
        if event.type == EventConfig.SHOW_MULTIPLY_OPTIONS_WAR:
            self.define_message()
        self.save_cache_values()

    # def define_board_stage(self):
    #     DataCache.get_value("")

    def read_cache_values(self):
        self._ships_status = DataCache.get_value("water_status")
        self._islands_status = DataCache.get_value("islands_status")
        self._warriors_status = DataCache.get_value("warriors_status")
        self._coins = DataCache.get_value("coins")
        self._heros = DataCache.get_value("hero_players")
        super().read_cache_values()

    def save_cache_values(self):
        DataCache.set_value("water_status", self._ships_status)
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
                self._ships_status[self.generate_unique_id()] = {
                    "owner": _player,
                    "num_of_entities": _num_of_entities,
                    "income": base_config["base_income"],
                    "field": circle,
                    # "location": Config.boards.circles_centers[circle]
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
                    "field": island
                }
            else:
                self._islands_status[island] = {
                    "owner": "None",
                    "num_of_entities": 0,
                    "base_income": base_config["base_income"],
                    "income": 0,
                    "building": {
                        "small": {
                            key: "" for key in base_config["buildings"]["small"]
                        },
                        "big": False
                    }
                }

    def generate_unique_id(self) -> int:
        current_time_microseconds = int(time.time() * 1000000) + random.randint(-1000, 1000)
        return current_time_microseconds

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
            "ship": "new_warrior_location"  # rename to ship
        }

    @property
    def fields_status(self):
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
        avalible_posejdon_jumps = DataCache.get_value("posejdon_move")
        distance = 1300
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
                    temp_distance = math.sqrt(
                        (location["location"][0] - centers_loc[center][0])**2 + (location["location"][1] - centers_loc[center][1])**2
                    )
                    new_place = field_id if temp_distance < distance else new_place
                    distance = temp_distance if temp_distance < distance else distance
        if new_place:
            self.update_graph_colors()
            entity_status = self.fields_status[type]
            entity_map_points = self.entities_points[type]
            if self._coins[entity_status[moving_entity_id]["owner"]] >= 1:
                if type == "warrior" and self.Graph.has_connection(
                    entity_status[moving_entity_id]["field"],
                    new_place,
                    entity_status[moving_entity_id]["owner"]
                ):
                    self.move_warrior(moving_entity, moving_entity_id, new_place, entity_map_points, entity_status)
                elif type == "ship":
                    pass
                else:
                    update_entity = DataCache.get_value("entity_update")
                    update_entity[moving_entity_id] = {
                        "location": entity_map_points[entity_status[moving_entity_id]["field"]],
                        "num_of_entities": entity_status[moving_entity_id]["num_of_entities"]
                    }
                    DataCache.set_value("entity_update", update_entity)
            self.clear_message()

    def move_warrior(self, moving_entity, moving_entity_id, new_place, entity_map_points, entity_status):
        entity_split = self.split_entity_number(
            moving_entity[moving_entity_id],
            self._warriors_status[moving_entity_id]
        )
        self.send_update_warrior(
            moving_entity_id,
            entity_map_points,
            entity_split[1],
            self._warriors_status[moving_entity_id]["field"]
        )
        if self.Graph.colors[new_place] == "None":
            self._warriors_status[self.generate_unique_id()] = {
                "owner": entity_status[moving_entity_id]["owner"],
                "num_of_entities": entity_split[0],
                "field": new_place
            }
            self._islands_status[
                self._warriors_status[moving_entity_id]["field"]
            ]["num_of_entities"] = entity_split[1]
            self._islands_status[new_place]["owner"] = entity_status[moving_entity_id]["owner"]

        elif self.Graph.colors[new_place] == entity_status[moving_entity_id]["owner"]:
            for id, warrior_status in self._warriors_status.items():
                if warrior_status["field"] == new_place:

                    self.send_update_warrior(
                        id,
                        entity_map_points,
                        warrior_status["num_of_entities"] + entity_split[0],
                        new_place
                    )
        else:
            attacker_warriors_count = entity_split[0]
            war_diff = attacker_warriors_count - self._islands_status[new_place]["num_of_entities"]
            defensive_warrior_id = ""
            for id, warrior_status in self._warriors_status.items():
                if warrior_status["field"] == new_place:
                    defensive_warrior_id = id

            if war_diff > 0:
                self._islands_status[new_place]["owner"] = entity_status[moving_entity_id]["owner"]
                self._warriors_status[self.generate_unique_id()] = {
                    "owner": entity_status[moving_entity_id]["owner"],
                    "num_of_entities": war_diff,
                    "field": new_place
                }
                self._islands_status[new_place]["owner"] = entity_status[moving_entity_id]["owner"]
                self.delete_entity(defensive_warrior_id)
                pass
            elif war_diff <= 0:
                war_diff = abs(war_diff)
                self.send_update_warrior(
                    defensive_warrior_id,
                    entity_map_points,
                    war_diff,
                    new_place
                )
            self._islands_status[new_place]["num_of_entities"] = war_diff

    def send_update_warrior(self, entity_id, map_points, entity_num_value, new_place):
        update_entity = DataCache.get_value("entity_update")
        update_entity[entity_id] = {
            "location": map_points[new_place],
            "num_of_entities": entity_num_value
        }
        self._warriors_status[entity_id]["field"] = new_place
        self._warriors_status[entity_id]["num_of_entities"] = entity_num_value
        self._islands_status[new_place]["num_of_entities"] = entity_num_value
        DataCache.set_value("entity_update", update_entity)

    @staticmethod
    def split_entity_number(moving_entity, base_entity_stat):
        return [
            moving_entity["num_of_entities"],
            base_entity_stat["num_of_entities"] - moving_entity["num_of_entities"]
        ]

    def delete_entity(self, entity_id):
        DataCache.set_value("entity_delete", [entity_id])

    def fill_graph(self):
        _water_config = Config.boards.water_config
        for ver in _water_config[str(DataCache.get_value("num_of_players"))].keys():
            self.Graph.add_vertex(ver, "None")
        _island_vertex = Config.boards.islands_config
        for ver in _island_vertex[str(DataCache.get_value("num_of_players"))].keys():
            self.Graph.add_vertex(ver, "None")
        for ver, ver_config in _water_config[str(DataCache.get_value("num_of_players"))].items():
            for neighbors in ver_config["neighbors"]:
                self.Graph.add_edge(ver, neighbors)
            for neighbors in ver_config["neighbors_island"]:
                self.Graph.add_edge(ver, neighbors)

    def update_graph_colors(self):
        island_colors = {key: values["owner"] for key, values in self._islands_status.items()}
        water_colors = {values["field"]: values["owner"] for _, values in self._ships_status.items()}
        fields_colors = island_colors | water_colors
        if self.Graph.colors != fields_colors:
            for key, color in fields_colors.items():
                self.Graph.set_vertex_color(key, color)

    def define_message(self):
        DataCache.set_value("message_board", "Select how many soldiers you want to use")

    def clear_message(self):
        DataCache.set_value("message_board", "")
