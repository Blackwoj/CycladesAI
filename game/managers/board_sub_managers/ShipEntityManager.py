from pygame import Surface
from pygame.event import Event
from ...enums.GameState import GameState
from ...DataCache import DataCache
from ...gui.common.Config import Config
from .EntityManager import EntityManager
from ...dataclasses.EntitiesDataClass import Entity


class ShipEntityManager(EntityManager):

    def __init__(self, screen: Surface, stage: GameState):
        super().__init__(screen, stage)
        self.available_posejdon_jumps = 0

    def handle_events(self, event: Event):
        pass

    def read_cache_values(self):
        self._water_status = DataCache.get_value("water_status")
        return super().read_cache_values()

    def save_cache_values(self):
        DataCache.set_value("water_status", self._water_status)
        return super().save_cache_values()

    @property
    def entity_type(self) -> str:
        return "ship"

    @property
    def filed_config(self):
        return Config.boards.water_config

    @property
    def new_entity_tag(self):
        return "new_ship_location"

    @property
    def entities_points(self):
        return Config.boards.circles_centers[self._num_of_players]

    @property
    def field_status(self):
        return self._water_status

    @property
    def valid_entity_move(self) -> bool:
        self.available_posejdon_jumps = DataCache.get_value("posejdon_move")
        return (
            self.available_posejdon_jumps > 0
            or self._coins[self.entity_status[self.moving_entity_id].owner]
        ) and (
            self.entity_status[self.moving_entity_id].location in self.filed_config[self._num_of_players][self.new_place]["neighbors"]
        )

    def entity_move_prepare(self):
        if self.available_posejdon_jumps == 0:
            if self._coins[self.entity_status[self.moving_entity_id].owner] == 0:
                self.send_update(
                    self.moving_entity_id,
                    self.entities_points,
                    self.entity_status[self.moving_entity_id].quantity,
                    self.entity_status[self.moving_entity_id].location
                )
                return
            self._coins[self.entity_status[self.moving_entity_id].owner] -= 1
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
            if island_status[island].owner == self._act_player:
                _is_valid_field = True
        if (
            _is_valid_field
            and self._coins[self._act_player] >= int(self.moving_entity_id) * -1
        ):
            _ship_added = False
            for entity_id, entity_data in self.entity_status.items():
                if entity_data.location == self.new_place:
                    self.send_update(
                        entity_id,
                        self.entities_points,
                        entity_data.quantity + 1,
                        self.new_place
                    )
                    _ship_added = True
            if not _ship_added:
                self.entity_status[self.generate_unique_id()] = Entity(
                    self.entity_type,
                    self._act_player,
                    1,
                    self.new_place
                )
                self.field_status[self.new_place].quantity = 1
                self.field_status[self.new_place].owner = self._act_player
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
