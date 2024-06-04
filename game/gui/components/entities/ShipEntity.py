import pygame

from ....DataCache import DataCache
from ....static.EventConfig import EventConfig
from .AbstractEntity import AbstractEntity
from ....enums.GameState import GameState


class ShipEntity(AbstractEntity):

    def __init__(
        self,
        entity_id: int,
        screen: pygame.Surface,
        island_point: list[int],
        num_of_entities: int,
        owner: str,
        warriors_icons: pygame.Surface,
        ownership_icon: pygame.Surface,
        multiply_icon: dict[int, pygame.Surface],
    ):
        super().__init__(
            entity_id,
            screen,
            island_point,
            num_of_entities,
            warriors_icons,
            multiply_icon,
            ownership_icon
        )
        self._owner = owner

    @property
    def icon_size(self) -> int:
        return 30

    def validate_move(self):
        loc = (self._act_location[0] + self.icon_size, self._act_location[1] + self.icon_size)
        DataCache.set_value(
            "new_ship_location",
            {self._id: {"location": loc, "num_of_entities": self._num_of_entities}}
        )
        pygame.event.post(pygame.event.Event(EventConfig.SHOW_MULTIPLY_OPTIONS_SHIP))

    @property
    def handle_mouse_validator(self) -> bool:
        return (
            DataCache.get_value("act_stage") != GameState.BOARD
            or self._num_of_entities == 0
            or DataCache.get_value("message_board")
            or DataCache.get_value("act_player") != self._owner
            or DataCache.get_value("act_hero") != "posejdon"
        )
