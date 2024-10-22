from copy import deepcopy

from pygame import Surface
from pygame.event import Event

from game.enums.GameState import GameState

from ...DataCache import DataCache
from ...dataclasses.BuildingDataClass import Building
from ...dataclasses.FieldDataClass import Fieldv2
from ...gui.common.Config import Config
from ...utilities.utilities import calc_distance
from ..AbstractManager import AbstractManager


class BuildingsEntityManager(AbstractManager):

    def __init__(self, screen: Surface, stage: GameState):
        super().__init__(screen)
        self.stage = stage

    def handle_events(self, _: Event):
        pass

    def stage_type(self):
        pass

    def read_cache_values(self):
        self._coins = DataCache.get_value("coins")
        self.fields_status: dict[str, Fieldv2] = DataCache.get_value("fields_status")
        self.building_location = DataCache.get_value("new_building")
        self.buildings_status = DataCache.get_value("buildings_status")
        return super().read_cache_values()

    def save_cache_values(self):
        DataCache.set_value("coins", self._coins)
        DataCache.set_value("fields_status", self.fields_status)
        DataCache.set_value("new_building", self.building_location)
        DataCache.set_value("buildings_status", self.buildings_status)
        return super().save_cache_values()

    @property
    def entity_type(self):
        return "building"

    @property
    def field_config(self):
        return Config.boards.buildings_centers[self._num_of_players]

    @property
    def new_entity_tag(self) -> DataCache.AvailableSections:
        return "new_building"

    def new_building_decider(self):
        self.read_cache_values()

        new_loc = ["", ""]
        closest_distance = Config.boards.default_max_len
        if DataCache.get_value("metro_building"):
            self.new_metro_decider()
            return
        for field_id, field_data in self.fields_status.items():
            if field_data.owner == self._act_player:
                for i in range(len(self.field_config[field_id]["small"])):
                    if field_data.small_building and not field_data.small_building[str(i + 1)]:
                        temp_loc = calc_distance(self.building_location, self.field_config[island_id]["small"][i])
                        new_loc = [field_id, str(i + 1)] if temp_loc < closest_distance else new_loc
                        closest_distance = temp_loc if temp_loc < closest_distance else closest_distance

        if closest_distance < 50 and self._coins[self._act_player] >= 2:
            self._coins[self._act_player] -= 2
            temp_id = self.generate_unique_id()
            self.buildings_status[temp_id] = Building(
                self._act_hero,
                self.field_config[new_loc[0]]["small"][int(new_loc[1]) - 1],
                new_loc[0],
                new_loc[1]
            )
            if self.fields_status[new_loc[0]].small_building is not None:
                self.fields_status[new_loc[0]].small_building[new_loc[1]] = self._act_hero  # type: ignore
        else:
            DataCache.set_value("reset_building", True)
        self.save_cache_values()

    def new_metro_decider(self):
        new_loc = ""
        closest_distance = Config.boards.default_max_len

        for island_id, island_data in self._islands_status.items():
            if island_data.owner == self._act_player:
                if not island_data.metropolis:
                    temp_loc = calc_distance(self.building_location, self.field_config[island_id]["big"])
                    new_loc = island_id if temp_loc < closest_distance else new_loc
                    closest_distance = temp_loc if temp_loc < closest_distance else closest_distance

        if closest_distance < 50:
            temp_id = self.generate_unique_id()
            self.delete_buildings()
            self.buildings_status[temp_id] = Building(
                "metro",
                self.field_config[new_loc]["big"],
                new_loc
            )
            self._islands_status[new_loc].metropolis = True
        else:
            DataCache.set_value("reset_building", True)
        self.save_cache_values()

    def check_if_metro(self):
        self.read_cache_values()
        building_status: dict[str, dict[str, int]] = deepcopy(Config.boards.calc_buildings_help_dict)
        for _, field_data in self.fields_status.items():
            if not field_data.buildings:
                continue
            for _, building in field_data.buildings.items():
                if building:
                    building_status[field_data.owner][building.hero] += 1
        for player, buildings_counted in building_status.items():
            if all(buildings_counted.values()) >= 1:
                if player == self._act_player:
                    return True
                else:
                    return False
        self.save_cache_values()

    def delete_buildings(self):
        buildings_to_delete: dict[str, int] = DataCache.get_value("building_to_delete")
        DataCache.set_value("entity_delete", list(buildings_to_delete.values()))
        delete_buildings_id = list(buildings_to_delete.values())
        for building_id, building_data in self.buildings_status.items():
            if building_id in delete_buildings_id:
                self._islands_status[building_data.island].small_building[building_data.place] = ""  # type: ignore
        for building_id in buildings_to_delete.values():
            self.buildings_status.pop(building_id)
        DataCache.set_value("building_to_delete", {})
        DataCache.set_value("metro_building", False)
