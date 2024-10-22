import pygame

from ....DataCache import DataCache
from ....dataclasses.IncomeDataClass import Income
from ....enums.GameState import GameState
from ....static.EventConfig import EventConfig
from .AbstractEntity import AbstractEntity


class IncomeEntity(AbstractEntity):

    def __init__(
        self,
        entity_id: int,
        screen: pygame.Surface,
        entity_data: Income,
        entity_location: str,
        income_icons: pygame.Surface,
        multiply_icon: dict[int, pygame.Surface],
        allow_drag: bool = False
    ):
        super().__init__(
            entity_id,
            screen,
            entity_data,
            "",
            entity_location,
            income_icons,
            multiply_icon
        )
        self._allow_drag = allow_drag

    @property
    def icon_size(self) -> int:
        return 15

    def validate_move(self):
        loc = (self._act_location[0] + self.icon_size, self._act_location[1] + self.icon_size)
        DataCache.set_value(
            "new_income_location",
            {
                "moving_entity_id": self._id,
                "map_location": loc,
            }
        )
        pygame.event.post(pygame.event.Event(EventConfig.UPDATE_INCOME_POS))

    @property
    def handle_mouse_validator(self) -> bool:
        return (
            DataCache.get_value("act_stage") != GameState.BOARD
            or self.entity_location == 0
            or DataCache.get_value("message_board")
            or DataCache.get_value("act_hero") != "apollon"
            or not self._allow_drag
        )
