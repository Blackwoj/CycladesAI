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
        # print(self.entity_status[self.moving_entity_id]["field"])
        # print(self.new_place)
        # print(self.entity_status[self.moving_entity_id]["owner"])
        # print(self.graph_warrior.has_connection(
        #     self.entity_status[self.moving_entity_id]["field"],
        #     self.new_place,
        #     self.entity_status[self.moving_entity_id]["owner"]))
        # print("graph colors")
        # print(self.graph_warrior.colors[self.entity_status[self.moving_entity_id]["field"]])
        # print(self.graph_warrior.colors[self.new_place])
        # print(self.graph_warrior.colors["F5"])
        # print(self.graph_warrior.colors["F6"])
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
