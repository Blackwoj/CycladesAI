import logging
from abc import abstractmethod
from typing import Any, Optional

from pygame import Surface
from pygame.event import Event

from ...DataCache import DataCache
from ...dataclasses.EntitiesDataClass import Entity
from ...dataclasses.FieldDataClass import Fieldv2
from ...dataclasses.PlayerDataClass import PlayerDataclass
from ...enums.GameState import GameState
from ...graph import Graph
from ...gui.common.Config import Config
from ...utilities.utilities import calc_distance
from .AbstractSubManager import AbstractSubManager


class EntityManager(AbstractSubManager):

    def __init__(self, screen: Surface, stage: GameState):
        super().__init__(screen, stage)
        self.graph_warrior = Graph()
        self.fill_graph()

    def handle_events(self, event: Event):
        pass

    @abstractmethod
    def read_cache_values(self):
        self._player_status: dict[str, PlayerDataclass] = DataCache.get_value("player_data")
        self.moving_entity: dict[str, Any] = DataCache.get_value(
            self.new_entity_tag
        )
        self.entity_to_delete = DataCache.get_value("entity_delete")
        self._fields_status: dict[str, Fieldv2] = DataCache.get_value("fields_status")
        return super().read_cache_values()

    @abstractmethod
    def save_cache_values(self):
        DataCache.set_value("player_data", self._player_status)
        DataCache.set_value("entity_delete", self.entity_to_delete)
        DataCache.set_value("fields_status", self._fields_status)
        return super().save_cache_values()

    @abstractmethod
    def add_new_entity(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def filed_config(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def entity_type(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def new_entity_tag(self) -> DataCache.AvailableSections:
        raise NotImplementedError

    @property
    @abstractmethod
    def entities_points(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def valid_entity_move(self) -> bool:
        raise NotImplementedError

    @property
    @abstractmethod
    def count_all_player_entity(self):
        raise NotImplementedError

    @abstractmethod
    def entity_move_prepare(self):
        raise NotImplementedError

    def valid_new_position(self):
        logging.info("Finding new location for entity")
        self.read_cache_values()
        centers_loc = Config.boards.circles_centers[self._num_of_players]

        distance = Config.boards.default_max_len
        self.moving_entity_id = self.moving_entity["moving_entity_id"]
        _previous_location = self.moving_entity["previous_location"]
        _new_map_location = self.moving_entity["map_location"]
        self.new_place = ""

        for field_id, field_config in self.filed_config.items():
            filed_to_check = []
            if "location" in field_config.keys():
                filed_to_check = field_config["location"]
            else:
                filed_to_check.append(field_id)
            for center in filed_to_check:
                temp_distance = calc_distance(_new_map_location, centers_loc[center])
                self.new_place = field_id if temp_distance < distance else self.new_place
                distance = temp_distance if temp_distance < distance else distance
        if not self.new_place:
            logging.info("No place found for entity!")
            DataCache.set_value("valid_ai_move", False)
            return
        logging.info("Found place: %s for entity", self.new_place)

        if self.moving_entity_id in [0, -1, -2, -3, -4]:
            self.add_new_entity()
            return

        if self.new_place:
            if self._player_status[self._fields_status[_previous_location].owner].coins >= 1:
                if self.valid_entity_move:
                    DataCache.set_value(
                        "move_train_data",
                        [
                            "move",
                            self.moving_entity["previous_location"],
                            self.new_place,
                            self.moving_entity["quantity"],
                        ]
                    )
                    self.entity_move_prepare()
                else:
                    update_entity = DataCache.get_value("entity_update")
                    update_entity[self.moving_entity_id] = {
                        "location": self.entities_points[_previous_location],
                        "quantity": self._fields_status[_previous_location].entity.quantity
                    }
                    DataCache.set_value("entity_update", update_entity)
                    DataCache.set_value("valid_ai_move", False)
                    logging.info("Wrong %s move", self.entity_type)
            else:
                update_entity = DataCache.get_value("entity_update")
                update_entity[self.moving_entity_id] = {
                    "location": self.entities_points[_previous_location],
                    "quantity": self._fields_status[_previous_location].entity.quantity
                }
                DataCache.set_value("entity_update", update_entity)
                logging.info("No enough money to move %s!", self.entity_type)
            self.clear_message()

    def update_graph_colors(self):
        fields_colors = {key: values.owner for key, values in self._fields_status.items()}
        if self.graph_warrior.colors != fields_colors:
            for key, color in fields_colors.items():
                self.graph_warrior.set_vertex_color(key, color)

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

    def clear_message(self):
        DataCache.set_value("message_board", "")

    def move_entity_define(self):
        _previous_location = self.moving_entity["previous_location"]
        entity_split = self.split_entity_number(
            self.moving_entity,
            self._fields_status[_previous_location].entity,
        )
        if not self.entity_type == "ship" and not entity_split[1] == 0:
            self.send_update(
                self.moving_entity_id,
                self.entities_points,
                entity_split[1],
                _previous_location
            )

        if self._fields_status[self.new_place].owner == "None":
            self._fields_status[self.new_place].entity = Entity(
                self.generate_unique_id(),
                self.entity_type,
                entity_split[0]
            )
            self._fields_status[self.new_place].owner = self._fields_status[_previous_location].owner
        elif self._fields_status[self.new_place].owner == self._fields_status[_previous_location].owner:
            self.send_update(
                self._fields_status[self.new_place].entity._id,
                self.entities_points,
                self._fields_status[self.new_place].entity.quantity + entity_split[0],
                self.new_place
            )
        else:
            attacker_entity_count = entity_split[0]
            war_diff = attacker_entity_count - self._fields_status[self.new_place].entity.quantity
            defensive_entity_id = ""
            defensive_entity_id = self._fields_status[self.new_place].entity._id
            if war_diff > 0:
                self._fields_status[self.new_place].entity = Entity(
                    self.generate_unique_id(),
                    self.entity_type,
                    war_diff
                )
                self._fields_status[self.new_place].owner = self._fields_status[_previous_location].owner
                self.entity_to_delete.append(defensive_entity_id)
            elif war_diff < 0 or war_diff == 0 and self.entity_type == "warrior":
                war_diff = abs(war_diff)
                self.send_update(
                    defensive_entity_id,
                    self.entities_points,
                    war_diff,
                    self.new_place
                )
            elif war_diff == 0 and self.entity_type == "ship":
                self.entity_to_delete.append(defensive_entity_id)
                self.entity_to_delete.append(self._fields_status[self.new_place].entity._id)
                self._fields_status[self.new_place].owner = ""
                self._fields_status[self.new_place].entity = Entity(None, None, 0)
            self._fields_status[self.new_place].entity.quantity = war_diff
        if self.entity_type == "ship" and entity_split[1] == 0:
            self.entity_to_delete.append(self.moving_entity_id)
            self._fields_status[_previous_location].entity = Entity(None, None, 0)
            self._fields_status[_previous_location].owner = "None"
        else:
            self._fields_status[_previous_location].entity.quantity = entity_split[1]
            self.send_update(
                self.moving_entity_id,
                self.entities_points,
                entity_split[1],
                _previous_location
            )
        self.save_cache_values()

    @staticmethod
    def split_entity_number(moving_entity, base_entity_stat):
        return [
            moving_entity["quantity"],
            base_entity_stat.quantity - moving_entity["quantity"]
        ]

    def send_update(self, entity_id, map_points, entity_num_value, new_place):
        update_entity = DataCache.get_value("entity_update")
        update_entity[entity_id] = {
            "location": map_points[new_place],
            "quantity": entity_num_value
        }
        for _, field_data in self._fields_status.items():
            if field_data.entity._id == entity_id:
                field_data.entity.quantity = entity_num_value
        DataCache.set_value("entity_update", update_entity)

    def essential_entity_data(self, entity_id: str) -> Optional[tuple[str, str, Entity]]:
        for _field_id, _field_data in self._fields_status.items():
            if not _field_data.entity or _field_data.entity._id != entity_id:
                continue
            return _field_id, _field_data.owner, _field_data.entity
