from pygame import Surface
from pygame.event import Event
from ...DataCache import DataCache
from ...gui.common.Config import Config
import math
from typing import List
from ..AbstractManager import AbstractManager
from ...dataclasses.IncomeDataClass import Income


class AppollonManager(AbstractManager):

    def __init__(self, screen: Surface):
        super().__init__(screen)

    def handle_events(self, event: Event):
        pass

    def stage_type(self):
        pass

    def read_cache_values(self):
        self._income_status = DataCache.get_value("income_status")
        self._island_status = DataCache.get_value("islands_status")
        self._water_status = DataCache.get_value("water_status")
        return super().read_cache_values()

    def save_cache_values(self):
        DataCache.set_value("income_status", self._income_status)
        DataCache.set_value("islands_status", self._island_status)
        return super().save_cache_values()

    def valid_new_position(self):
        self.read_cache_values()
        distance = 1300000
        self.new_place = ""
        self.moving_entity_id = ""
        for _id, location in self.moving_entity.items():
            self.moving_entity_id = _id
            for field_id, field_center in self.fields_config.items():
                temp_distance = self.calc_len(location["location"], field_center)
                self.new_place = field_id if temp_distance < distance else self.new_place
                distance = temp_distance if temp_distance < distance else distance
        if self.new_place:
            self._island_status[self.new_place].income += 1
            found = False
            for id, income_config in self._income_status.items():
                if income_config.location == self.new_place:
                    self._income_status[id].quantity += 1
                    found = True,
                    entity_to_update = DataCache.get_value("entity_update")
                    entity_to_update[id] = {
                        "location": self.fields_config[self.new_place],
                        "num_of_entities": self._island_status[self.new_place].income
                    }
                    DataCache.set_value("entity_update", entity_to_update)
            if not found:
                self._income_status[self.generate_unique_id()] = Income(
                    self._island_status[self.new_place].income,
                    self.new_place
                )
            entity_to_delete = DataCache.get_value("entity_delete")
            entity_to_delete.append(2)
            DataCache.set_value("entity_delete", entity_to_delete)

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
