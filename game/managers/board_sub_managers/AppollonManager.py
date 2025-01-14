import math
from typing import List

from pygame import Surface
from pygame.event import Event

from ...DataCache import DataCache
from ...dataclasses.FieldDataClass import Fieldv2
from ...gui.common.Config import Config
from ..AbstractManager import AbstractManager


class AppollonManager(AbstractManager):

    def __init__(self, screen: Surface):
        super().__init__(screen)

    def handle_events(self, event: Event):
        pass

    def stage_type(self):
        pass

    def read_cache_values(self):
        self._field_status: dict[str, Fieldv2] = DataCache.get_value("fields_status")
        return super().read_cache_values()

    def save_cache_values(self):
        DataCache.set_value("fields_status", self._field_status)
        return super().save_cache_values()

    def valid_new_position(self):
        self.read_cache_values()
        distance = 1300000
        self.new_place = ""
        self.moving_entity_id = self.moving_entity["moving_entity_id"]
        for field_id, field_center in self.fields_config.items():
            temp_distance = self.calc_len(self.moving_entity["map_location"], field_center)
            self.new_place = field_id if temp_distance < distance else self.new_place
            distance = temp_distance if temp_distance < distance else distance
        if (
            self.new_place
            and distance < 80
            and self._act_player == self._field_status[self.new_place].owner
        ):
            DataCache.set_value("move_train_data", ["income_place", self.new_place])
            DataCache.set_value("valid_ai_move", True)
            self._field_status[self.new_place].income.quantity += 1
            if self._field_status[self.new_place].income._id == 2:
                self._field_status[self.new_place].income._id = self.generate_unique_id()
            else:
                entity_to_update = DataCache.get_value("entity_update")
                entity_to_update[self._field_status[self.new_place].income._id] = {
                    "location": self.fields_config[self.new_place],
                    "quantity": self._field_status[self.new_place].income.quantity
                }
                DataCache.set_value("entity_update", entity_to_update)
            entity_to_delete = DataCache.get_value("entity_delete")
            entity_to_delete.append(2)
            DataCache.set_value("entity_delete", entity_to_delete)
        else:
            DataCache.set_value("reset_building", True)
            DataCache.set_value("valid_ai_move", False)

    @property
    def moving_entity(self) -> dict:
        return DataCache.get_value("new_income_location")

    @property
    def fields_config(self):
        return Config.boards.income_point[self._num_of_players]

    def calc_len(self, dest_loc: List[int], point_loc: List[int]):
        return math.sqrt(
            (dest_loc[0] - point_loc[0])**2 + (dest_loc[1] - point_loc[1])**2
        )
