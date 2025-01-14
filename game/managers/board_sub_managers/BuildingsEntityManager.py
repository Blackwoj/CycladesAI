import logging
from copy import deepcopy

from pygame import Surface
from pygame.event import Event

from game.enums.GameState import GameState

from ...DataCache import DataCache
from ...dataclasses.BuildingDataClass import Building
from ...dataclasses.FieldDataClass import Fieldv2
from ...dataclasses.PlayerDataClass import PlayerDataclass
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
        self._player_status: dict[str, PlayerDataclass] = DataCache.get_value("player_data")
        self.fields_status: dict[str, Fieldv2] = DataCache.get_value("fields_status")
        self.building_location = DataCache.get_value("new_building_location")
        return super().read_cache_values()

    def save_cache_values(self):
        DataCache.set_value("player_data", self._player_status)
        DataCache.set_value("fields_status", self.fields_status)
        DataCache.set_value("new_building_location", self.building_location)
        return super().save_cache_values()

    @property
    def entity_type(self):
        return "building"

    @property
    def field_config(self):
        return Config.boards.buildings_centers[self._num_of_players]

    @property
    def new_entity_tag(self) -> DataCache.AvailableSections:
        return "new_building_location"

    def new_building_decider(self):
        self.read_cache_values()

        new_loc = ["", ""]
        closest_distance = Config.boards.default_max_len
        if DataCache.get_value("metro_building_philo") or DataCache.get_value("metro_building_build"):
            self.new_metro_decider()
            return
        for field_id, field_data in self.fields_status.items():
            if field_data.type == "island" and field_data.owner == self._act_player:
                for i in range(len(self.field_config[field_id]["small"])):
                    if field_data.buildings and not field_data.buildings[str(i + 1)]:
                        temp_loc = calc_distance(self.building_location, self.field_config[field_id]["small"][i])
                        new_loc = [field_id, str(i + 1)] if temp_loc < closest_distance else new_loc
                        closest_distance = temp_loc if temp_loc < closest_distance else closest_distance
        if (
            closest_distance < 50
            and self._player_status[self._act_player].coins >= 2
            and (
                not self.fields_status[new_loc[0]].metropolis[0]
                or self._if_place_free(new_loc)
            )
        ):
            self._player_status[self._act_player].coins -= 2
            DataCache.set_value("move_train_data", ["build", new_loc[0], new_loc[1]])
            DataCache.set_value("valid_ai_move", True)
            self.fields_status[new_loc[0]].buildings[new_loc[1]] = Building(  # type: ignore
                self.generate_unique_id(),
                self._act_hero,
                self.field_config[new_loc[0]]["small"][int(new_loc[1]) - 1]
            )
        else:
            DataCache.set_value("reset_building", True)
            DataCache.set_value("valid_ai_move", False)
        self.save_cache_values()

    def new_metro_decider(self):
        new_loc = ""
        closest_distance = Config.boards.default_max_len
        for field_id, field_data in self.fields_status.items():
            if field_data.owner != self._act_player or field_data.metropolis[0] or field_data.type != "island":
                continue
            temp_loc = calc_distance(self.building_location, self.field_config[field_id]["big"])
            new_loc = field_id if temp_loc < closest_distance else new_loc
            closest_distance = temp_loc if temp_loc < closest_distance else closest_distance
        if (
            closest_distance < 50
            and self.check_if_build_metro_possible(
                new_loc,
                list(DataCache.get_value("building_to_delete").values())
            )
        ):
            DataCache.set_value("move_train_data", [
                "metro_build",
                new_loc,
                DataCache.get_value("building_to_delete")
            ])
            self.delete_buildings()
            self.fields_status[new_loc].metropolis = (
                True,
                Building(
                    self.generate_unique_id(),
                    "metro",
                    self.field_config[new_loc]["big"]
                )
            )
        else:
            DataCache.set_value("valid_ai_move", False)
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
        entity_to_delete = DataCache.get_value("entity_delete")
        DataCache.set_value("entity_delete", list(buildings_to_delete.values()) + entity_to_delete)

        delete_buildings_id = list(buildings_to_delete.values())
        for field_id, field_data in self.fields_status.items():
            if isinstance(field_data.buildings, dict):
                for place, building in field_data.buildings.items():
                    if building and building._id in delete_buildings_id:
                        field_data.buildings[place] = None
        DataCache.set_value("building_to_delete", {})
        DataCache.set_value("metro_building_philo", False)
        DataCache.set_value("metro_building_build", False)

    def check_if_build_metro_possible(self, field_id, building_to_delete_ids) -> bool:
        islands_config = Config.boards.islands_config[str(DataCache.get_value("num_of_players"))]
        for place in islands_config[field_id]["buildings"]["big"][0]:
            if not self.fields_status[field_id].buildings[place] or self.fields_status[field_id].buildings[place]._id in building_to_delete_ids:  # type: ignore
                continue
            else:
                logging.info("Deleting building on metro place!")
                entity_to_delete: list = DataCache.get_value("entity_delete")
                entity_to_delete.append(self.fields_status[field_id].buildings[place]._id)  # type: ignore
                self.fields_status[field_id].buildings[place] = None  # type: ignore
                continue
        return True

    def _if_place_free(self, new_place: list):
        islands_config = Config.boards.islands_config[str(DataCache.get_value("num_of_players"))]
        metro_place_on_island = islands_config[new_place[0]]["buildings"]["big"][0]
        if new_place[1] in metro_place_on_island:
            return False
        return True
