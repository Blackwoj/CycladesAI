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

    def valid_entity_move(self) -> bool:
        return (
            self.available_posejdon_jumps > 0
            or self._coins[self.entity_status[self.moving_entity_id]["owner"]]
        ) and (
            self._ships_status[self.moving_entity_id]["field"] in self.filed_config[type][self._num_of_players][self.new_place]["neighbors"]
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
