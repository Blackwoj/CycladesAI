from pygame import Surface
from pygame.event import Event

from ...DataCache import DataCache
from ...enums.GameState import GameState
from ...gui.common.Config import Config
from .EntityManager import EntityManager


class WarriorEntityManager(EntityManager):

    def __init__(self, screen: Surface, stage: GameState):
        super().__init__(screen, stage)

    def handle_events(self, event: Event):
        pass

    def read_cache_values(self):
        return super().read_cache_values()

    def save_cache_values(self):
        return super().save_cache_values()

    @property
    def entity_type(self) -> str:
        return "warrior"

    @property
    def filed_config(self):
        return Config.boards.islands_config[self._num_of_players]

    @property
    def new_entity_tag(self) -> str:
        return "new_warrior_location"

    @property
    def entities_points(self):
        return Config.boards.warriors_points[self._num_of_players]

    @property
    def valid_entity_move(self) -> bool:
        self.update_graph_colors()
        for field_id, field_data in self._fields_status.items():
            if field_data.entity._id == self.moving_entity_id:
                return self.graph_warrior.has_connection(
                    field_id,
                    self.new_place,
                    field_data.owner
                )
        return False

    def entity_move_prepare(self):
        for _, field_data in self._fields_status.items():
            if field_data.entity._id == self.moving_entity_id:
                self._coins[field_data.owner] -= 1
                self.move_entity_define()

    def add_new_entity(self):
        if (
            self._fields_status[self.new_place].owner == self._act_player
            and self._coins[self._act_player] >= int(self.moving_entity_id) * -1
        ):
            self.send_update(
                self._fields_status[self.new_place].entity._id,
                self.entities_points,
                self._fields_status[self.new_place].entity.quantity + 1,
                self.new_place
            )

            self._coins[self._act_player] -= DataCache.get_value("new_entity_price")

            if DataCache.get_value("new_entity_price") <= 4:
                new_price = int(self.moving_entity_id) * (-1) + 1
                if new_price == 1:
                    new_price += 1
                DataCache.set_value("new_entity_price", new_price)
        else:
            update_entity = DataCache.get_value("entity_update")
            update_entity[self.moving_entity_id] = {
                "location": Config.boards.new_special_event_loc,
                "quantity": 1
            }
            DataCache.set_value("entity_update", update_entity)
