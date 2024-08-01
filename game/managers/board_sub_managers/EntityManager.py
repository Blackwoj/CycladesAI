from pygame import Surface
from pygame.event import Event
from .AbstractSubManager import AbstractSubManager
from ...enums.GameState import GameState
from ...DataCache import DataCache
from ...gui.common.Config import Config
from abc import abstractmethod
import logging
from ...graph import Graph
from ...dataclasses.EntitiesDataClass import Entity
from ...utilities.utilities import calc_distance


class EntityManager(AbstractSubManager):

    def __init__(self, screen: Surface, stage: GameState):
        super().__init__(screen, stage)
        self.graph_warrior = Graph()
        self.fill_graph()

    def handle_events(self, event: Event):
        pass

    @abstractmethod
    def read_cache_values(self):
        self._coins = DataCache.get_value("coins")
        self.moving_entity = DataCache.get_value(self.new_entity_tag)
        self.entity_to_delete = DataCache.get_value("entity_delete")
        self.entity_status = DataCache.get_value("entities_status")
        return super().read_cache_values()

    @abstractmethod
    def save_cache_values(self):
        DataCache.set_value("entities_status", self.entity_status)
        DataCache.set_value("coins", self._coins)
        DataCache.set_value("entity_delete", self.entity_to_delete)
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
    def field_status(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def valid_entity_move(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def entity_move_prepare(self):
        raise NotImplementedError

    def valid_new_position(self):
        self.read_cache_values()
        centers_loc = Config.boards.circles_centers[self._num_of_players]

        distance = Config.boards.default_max_len
        self.moving_entity_id = ""
        self.new_place = ""

        for _id, location in self.moving_entity.items():
            self.moving_entity_id = _id
            for field_id, field_config in self.filed_config[self._num_of_players].items():
                filed_to_check = []
                if "location" in field_config.keys():
                    filed_to_check = field_config["location"]
                else:
                    filed_to_check.append(field_id)
                for center in filed_to_check:
                    temp_distance = calc_distance(location["location"], centers_loc[center])
                    self.new_place = field_id if temp_distance < distance else self.new_place
                    distance = temp_distance if temp_distance < distance else distance

        if self.moving_entity_id in [0, -1, -2, -3, -4]:
            self.add_new_entity()
            return

        if self.new_place:
            self.update_graph_colors()
            if self._coins[self.entity_status[self.moving_entity_id].owner] >= 1:
                if self.valid_entity_move:
                    self.entity_move_prepare()
                else:
                    update_entity = DataCache.get_value("entity_update")
                    update_entity[self.moving_entity_id] = {
                        "location": self.entities_points[self.entity_status[self.moving_entity_id].location],
                        "quantity": self.entity_status[self.moving_entity_id].quantity
                    }
                    DataCache.set_value("entity_update", update_entity)
                    logging.info("Wrong entity move", self.entity_type)
            else:
                update_entity = DataCache.get_value("entity_update")
                update_entity[self.moving_entity_id] = {
                    "location": self.entities_points[self.entity_status[self.moving_entity_id].location],
                    "quantity": self.entity_status[self.moving_entity_id].quantity
                }
                DataCache.set_value("entity_update", update_entity)
                logging.info("No enough money to move %s!", self.entity_type)
            self.clear_message()

    def update_graph_colors(self):
        _water_config = DataCache.get_value("water_status")
        fields_colors = {key: values.owner for key, values in self.field_status.items()}
        water_colors = {key: values.owner for key, values in _water_config.items()}
        fields_colors = fields_colors | water_colors
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

    def move_entity_define(
        self,
        moving_entity,
        moving_entity_id,
        new_place,
        entity_map_points,
        entity_status
    ):
        entity_split = self.split_entity_number(
            moving_entity[moving_entity_id],
            self.entity_status[moving_entity_id]
        )
        self.send_update(
            moving_entity_id,
            entity_map_points,
            entity_split[1],
            self.entity_status[moving_entity_id].location
        )
        if self.entity_type == "ship" and entity_split[1] == 0:
            self.entity_to_delete.append(moving_entity_id)
            self.field_status[self.entity_status[moving_entity_id].location].owner = "None"
            self.field_status[self.entity_status[moving_entity_id].location].quantity = 0
        else:
            self.field_status[
                self.entity_status[moving_entity_id].location
            ].quantity = entity_split[1]
        if self.field_status[new_place].owner == "None":
            self.entity_status[self.generate_unique_id()] = Entity(
                self.entity_type,
                entity_status[moving_entity_id].owner,
                entity_split[0],
                new_place
            )
            self.field_status[new_place].owner = entity_status[moving_entity_id].owner
        elif self.field_status[new_place].owner == entity_status[moving_entity_id].owner:
            for id, entity_data in self.entity_status.items():
                if entity_data.location == new_place:

                    self.send_update(
                        id,
                        entity_map_points,
                        entity_data.quantity + entity_split[0],
                        new_place
                    )
        else:
            attacker_entity_count = entity_split[0]
            war_diff = attacker_entity_count - self.field_status[new_place].quantity
            defensive_entity_id = ""
            for id, entity_data in self.entity_status.items():
                if entity_data.location == new_place:
                    defensive_entity_id = id
            if war_diff > 0:
                self.entity_status[self.generate_unique_id()] = Entity(
                    self.entity_type,
                    entity_status[moving_entity_id].owner,
                    war_diff,
                    new_place
                )
                self.field_status[new_place].owner = entity_status[moving_entity_id].owner
                self.entity_to_delete.append(defensive_entity_id)
            elif war_diff <= 0:
                war_diff = abs(war_diff)
                self.send_update(
                    defensive_entity_id,
                    entity_map_points,
                    war_diff,
                    new_place
                )
            if war_diff == 0 and self.entity_type == "ship":
                self.entity_to_delete.append(defensive_entity_id)
            self.field_status[new_place].quantity = war_diff
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
        self.entity_status[entity_id].location = new_place
        self.entity_status[entity_id].quantity = entity_num_value
        self.field_status[new_place].quantity = entity_num_value
        DataCache.set_value("entity_update", update_entity)
