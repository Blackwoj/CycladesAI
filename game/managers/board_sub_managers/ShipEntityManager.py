from pygame import Surface
from pygame.event import Event
from ...enums.GameState import GameState
from ...DataCache import DataCache
from ...gui.common.Config import Config
from .EntityManager import EntityManager


class ShipEntityManager(EntityManager):

    def __init__(self, screen: Surface, stage: GameState):
        super().__init__(screen, stage)
        self.available_posejdon_jumps = 0

    def handle_events(self, event: Event):
        pass

    def read_cache_values(self):
        self._ships_status = DataCache.get_value("ship_status")
        self._water_status = DataCache.get_value("water_status")
        return super().read_cache_values()

    def save_cache_values(self):
        DataCache.set_value("ship_status", self._ships_status)
        DataCache.set_value("water_status", self._water_status)
        return super().save_cache_values()

    @property
    def entity_type(self) -> str:
        return "ship"

    @property
    def filed_config(self):
        return Config.boards.water_config

    @property
    def new_entity(self):
        return "new_ship_location"

    @property
    def entity_status(self):
        return self._ships_status

    @property
    def entities_points(self):
        return Config.boards.circles_centers[self._num_of_players]

    @property
    def field_status(self):
        return self._water_status

    @property
    def valid_entity_move(self) -> bool:
        return (
            self.available_posejdon_jumps > 0
            or self._coins[self.entity_status[self.moving_entity_id]["owner"]]
        ) and (
            self._ships_status[self.moving_entity_id]["field"] in self.filed_config[self._num_of_players][self.new_place]["neighbors"]
        )

    def entity_move_prepare(self):
        if self.available_posejdon_jumps == 0:
            self._coins[self.entity_status[self.moving_entity_id]["owner"]] -= 1
            DataCache.set_value("posejdon_move", 2)
        else:
            DataCache.set_value("posejdon_move", self.available_posejdon_jumps - 1)
        self.move_entity_define(
            self.moving_entity,
            self.moving_entity_id,
            self.new_place,
            self.entities_points,
            self.entity_status
        )

    def add_new_entity(self):
        island_status = DataCache.get_value("islands_status")
        neighbors_island = self.filed_config[self._num_of_players][self.new_place]["neighbors_island"]
        _is_valid_field = False
        for island in neighbors_island:
            if island_status[island]["owner"] == self._act_player:
                _is_valid_field = True
        if (
            _is_valid_field
            and self._coins[self._act_player] >= int(self.moving_entity_id) * -1
        ):
            _ship_added = False
            for entity_id, entity_data in self.entity_status.items():
                if entity_data["field"] == self.new_place:
                    self.send_update(
                        entity_id,
                        self.entities_points,
                        entity_data["num_of_entities"] + 1,
                        self.new_place
                    )
                    _ship_added = True
            if not _ship_added:
                self.entity_status[self.generate_unique_id()] = {
                    "owner": self._act_player,
                    "num_of_entities": 1,
                    "field": self.new_place
                }
            self._coins[self._act_player] -= DataCache.get_value("new_entity_price")

            if DataCache.get_value("new_entity_price") <= 3:
                new_price = int(self.moving_entity_id) * (-1) + 1

                DataCache.set_value("new_entity_price", new_price)
