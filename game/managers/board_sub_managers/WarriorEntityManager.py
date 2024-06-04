from pygame import Surface
from pygame.event import Event
from ...enums.GameState import GameState
from ...DataCache import DataCache
from ...gui.common.Config import Config
from .EntityManager import EntityManager


class WarriorEntityManager(EntityManager):

    def __init__(self, screen: Surface, stage: GameState):
        super().__init__(screen, stage)

    def handle_events(self, event: Event):
        pass

    def read_cache_values(self):
        self._warriors_status = DataCache.get_value("warriors_status")
        self._islands_status = DataCache.get_value("islands_status")
        return super().read_cache_values()

    def save_cache_values(self):
        DataCache.set_value("warriors_status", self._warriors_status)
        DataCache.set_value("islands_status", self._islands_status)
        return super().save_cache_values()

    @property
    def entity_type(self) -> str:
        return "warrior"

    @property
    def filed_config(self):
        return Config.boards.islands_config

    @property
    def new_entity(self) -> str:
        return "new_warrior_location"

    @property
    def entity_status(self):
        return self._warriors_status

    @property
    def entities_points(self):
        return Config.boards.warriors_points[self._num_of_players]

    @property
    def field_status(self):
        return self._islands_status

    @property
    def valid_entity_move(self) -> bool:
        self.update_graph_colors()
        return self.graph_warrior.has_connection(
            self.entity_status[self.moving_entity_id]["field"],
            self.new_place,
            self.entity_status[self.moving_entity_id]["owner"])

    def entity_move_prepare(self):
        self._coins[self.entity_status[self.moving_entity_id]["owner"]] -= 1
        self.move_entity_define(
            self.moving_entity,
            self.moving_entity_id,
            self.new_place,
            self.entities_points,
            self.entity_status
        )

    def add_new_entity(self):
        if (
            self.field_status[self.new_place]["owner"] == self._act_player
            and self._coins[self._act_player] >= int(self.moving_entity_id) * -1
        ):
            for entity_id, entity_data in self.entity_status.items():
                if entity_data["field"] == self.new_place:
                    self.send_update(
                        entity_id,
                        self.entities_points,
                        entity_data["num_of_entities"] + 1,
                        self.new_place
                    )

            print(DataCache.get_value("new_entity_price"))
            self._coins[self._act_player] -= DataCache.get_value("new_entity_price")

            if DataCache.get_value("new_entity_price") <= 4:
                new_price = int(self.moving_entity_id) * (-1) + 1
                if new_price == 1:
                    new_price += 1
                print("new price", new_price)
                DataCache.set_value("new_entity_price", new_price)
