import pygame

from ....DataCache import DataCache
from ....enums.GameState import GameState
from .AbstractEntity import AbstractEntity
from ....static.EventConfig import EventConfig
from ....dataclasses.IncomeDataClass import Income


class IncomeEntity(AbstractEntity):

    def __init__(
        self,
        entity_id: int,
        screen: pygame.Surface,
        entity_data: Income,
        income_icons: pygame.Surface,
        multiply_icon: dict[int, pygame.Surface],
        allow_drag: bool = False
    ):
        super().__init__(
            entity_id,
            screen,
            entity_data,
            income_icons,
            multiply_icon,
        )
        self._allow_drag = allow_drag

    @property
    def icon_size(self) -> int:
        return 15

    def validate_move(self):
        loc = (self._act_location[0] + self.icon_size, self._act_location[1] + self.icon_size)
        DataCache.set_value(
            "new_income_location",
            {self._id: {"location": loc, "num_of_entities": self.entity_data.location}}
        )
        pygame.event.post(pygame.event.Event(EventConfig.UPDATE_INCOME_POS))

    @property
    def handle_mouse_validator(self) -> bool:
        return (
            DataCache.get_value("act_stage") != GameState.BOARD
            or self.entity_data.location == 0
            or DataCache.get_value("message_board")
            or DataCache.get_value("act_hero") != "apollon"
            or not self._allow_drag
        )
