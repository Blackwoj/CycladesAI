import pygame

from ....DataCache import DataCache
from ....dataclasses.EntitiesDataClass import Entity
from ....enums.GameState import GameState
from ....static.EventConfig import EventConfig
from .AbstractEntity import AbstractEntity


class ShipEntity(AbstractEntity):

    def __init__(
        self,
        entity_id: int,
        screen: pygame.Surface,
        entity_data: Entity,
        entity_owner: str,
        entity_location: str,
        ship_icon: dict[str, dict[str, pygame.Surface]],
        ownership_icon: dict[str, pygame.Surface],
        multiply_icon: dict[int, pygame.Surface],
    ):
        super().__init__(
            entity_id,
            screen,
            entity_data,
            entity_owner,
            entity_location,
            ship_icon[str(entity_data._type)][entity_owner],
            multiply_icon,
            ownership_icon[str(entity_owner)]
        )

    @property
    def icon_size(self) -> int:
        return 30

    def validate_move(self):
        loc = (self._act_location[0] + self.icon_size, self._act_location[1] + self.icon_size)
        DataCache.set_value(
            "new_ship_location",
            {
                "moving_entity_id": self._id,
                "previous_location": self.entity_location,
                "map_location": loc,
                "quantity": self.entity_data.quantity
            }
        )
        pygame.event.post(pygame.event.Event(EventConfig.SHOW_MULTIPLY_OPTIONS_SHIP))

    @property
    def handle_mouse_validator(self) -> bool:
        return (
            DataCache.get_value("act_stage") != GameState.BOARD
            or self.entity_data.quantity == 0
            or DataCache.get_value("message_board")
            or DataCache.get_value("act_player") != self.entity_owner
            or DataCache.get_value("act_hero") != "posejdon"
        )
