from pygame import Surface
from game.enums.GameState import GameState
from ..AbstractManager import AbstractManager
from pygame.event import Event
from ...DataCache import DataCache
from ...gui.common.Config import Config
from ...dataclasses.BuildingDataClass import Building
from ...utilities.utilities import calc_distance
from ...dataclasses.FieldDataClass import Field
from copy import deepcopy


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
        self._islands_status: dict[str, Field] = DataCache.get_value("islands_status")
        self.building_location = DataCache.get_value("new_building")
        self.buildings_status = DataCache.get_value("buildings_status")
        return super().read_cache_values()

    def save_cache_values(self):
        DataCache.set_value("coins", self._coins)
        DataCache.set_value("islands_status", self._islands_status)
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

        for island_id, island_data in self._islands_status.items():
            if island_data.owner == self._act_player:
                for i in range(len(self.field_config[island_id]["small"])):
                    if island_data.small_building and not island_data.small_building[str(i + 1)]:
                        temp_loc = calc_distance(self.building_location, self.field_config[island_id]["small"][i])
                        new_loc = [island_id, str(i + 1)] if temp_loc < closest_distance else new_loc
                        closest_distance = temp_loc if temp_loc < closest_distance else closest_distance

        if closest_distance < 50 and self._coins[self._act_player] >= 2:
            self._coins[self._act_player] -= 2
            temp_id = self.generate_unique_id()
            self.buildings_status[temp_id] = Building(
                self._act_hero,
                self.field_config[new_loc[0]]["small"][int(new_loc[1]) - 1],
                new_loc[0]
            )
            if self._islands_status[new_loc[0]].small_building is not None:
                self._islands_status[new_loc[0]].small_building[new_loc[1]] = self._act_hero  # type: ignore
            if self.check_if_metro():
                DataCache.set_value("metro_building", True)
        else:
            DataCache.set_value("reset_building", True)
        self.save_cache_values()

    def check_if_metro(self):
        building_status: dict[str, dict[str, int]] = deepcopy(Config.boards.calc_buildings_help_dict)
        for _, island_data in self._islands_status.items():
            if not island_data.small_building:
                continue
            for _, building in island_data.small_building.items():
                if building:
                    building_status[island_data.owner][building] += 1
        for player, buildings_counted in building_status.items():
            if all(buildings_counted.values()) >= 1:
                return player
