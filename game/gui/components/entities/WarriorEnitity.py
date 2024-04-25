from .AbstractEntity import AbstractEntity
import pygame
from ....DataCache import DataCache
from ....static.EventConfig import EventConfig


class WarriorEntity(AbstractEntity):

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
            owner,
            warriors_icons,
            multiply_icon,
            ownership_icon
        )

    def validate_move(self):
        loc = (self._act_location[0] + 40, self._act_location[1] + 40)
        DataCache.set_value(
            "new_warrior_location",
            {self._id: {"location": loc, "num_of_entities": self._num_of_entities}}
        )
        pygame.event.post(pygame.event.Event(EventConfig.SHOW_MULTIPLY_OPTIONS_WAR))
