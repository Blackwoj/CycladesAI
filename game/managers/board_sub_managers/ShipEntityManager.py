from pygame import Surface
from pygame.event import Event

from ...DataCache import DataCache
from ...dataclasses.EntitiesDataClass import Entity
from ...enums.GameState import GameState
from ...gui.common.Config import Config
from .EntityManager import EntityManager


class ShipEntityManager(EntityManager):

    def __init__(self, screen: Surface, stage: GameState):
        super().__init__(screen, stage)
        self.available_posejdon_jumps = 0

    def handle_events(self, event: Event):
        pass

    def read_cache_values(self):
        return super().read_cache_values()

    def save_cache_values(self):
        return super().save_cache_values()

    @property
    def entity_type(self) -> str:
        return "ship"

    @property
    def filed_config(self):
        return Config.boards.water_config[self._num_of_players]

    @property
    def new_entity_tag(self):
        return "new_ship_location"

    @property
    def entities_points(self):
        return Config.boards.circles_centers[self._num_of_players]

    @property
    def valid_entity_move(self) -> bool:
        self.available_posejdon_jumps = DataCache.get_value("posejdon_move")
        return (
            self.moving_entity["previous_location"] in self.filed_config[self.new_place]["neighbors"]
        )

    def entity_move_prepare(self):
        if self.available_posejdon_jumps == 0:
            if self._coins[self._fields_status[self.moving_entity["previous_location"]].owner] == 0:
                self.send_update(
                    self.moving_entity_id,
                    self.entities_points,
                    self._fields_status[self.moving_entity["previous_location"]].entity.quantity,
                    self.moving_entity["previous_location"]
                )
                return
            self._coins[self._fields_status[self.moving_entity["previous_location"]].owner] -= 1
            DataCache.set_value("posejdon_move", 2)
        else:
            DataCache.set_value("posejdon_move", self.available_posejdon_jumps - 1)
        self.move_entity_define()

    def add_new_entity(self):
        neighbors_island = self.filed_config[self.new_place]["neighbors_island"]
        _is_valid_field = False
        for island in neighbors_island:
            if self._fields_status[island].owner == self._act_player:
                _is_valid_field = True
        if (
            _is_valid_field
            and self._coins[self._act_player] >= int(self.moving_entity_id) * -1
        ):
            _ship_added = False
            if self._fields_status[self.new_place].entity._id:
                self.send_update(
                    self._fields_status[self.new_place].entity._id,
                    self.entities_points,
                    self._fields_status[self.new_place].entity.quantity + 1,
                    self.new_place
                )
                _ship_added = True
            if not _ship_added:
                self._fields_status[self.new_place].entity = Entity(
                    self.generate_unique_id(),
                    self.entity_type,
                    1
                )
                self._fields_status[self.new_place].owner = self._act_player
            self._coins[self._act_player] -= DataCache.get_value("new_entity_price")
            if DataCache.get_value("new_entity_price") <= 3:
                new_price = int(self.moving_entity_id) * (-1) + 1
                DataCache.set_value("new_entity_price", new_price)
        else:
            update_entity = DataCache.get_value("entity_update")
            update_entity[self.moving_entity_id] = {
                "location": Config.boards.new_special_event_loc,
                "quantity": 1
            }
            DataCache.set_value("entity_update", update_entity)
