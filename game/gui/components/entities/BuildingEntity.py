import math

import pygame

from ....DataCache import DataCache
from ....enums.GameState import GameState
from ....static.EventConfig import EventConfig


class BuildingEntity(pygame.sprite.Sprite):

    def __init__(
        self,
        entity_id: int,
        screen: pygame.Surface,
        map_point: list[int],
        entity_icon: pygame.Surface,
        if_dragging: bool
    ):
        self._id = entity_id
        self.screen = screen
        self._map_point = map_point
        self._act_location = (self._map_point[0] - 20, self._map_point[1] - 20)
        self._if_dragging = if_dragging
        self.is_dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        super().__init__()
        self.image = entity_icon
        self.rect = self.image.get_rect()
        self.rect.topleft = self._act_location

    @property
    def entity_id(self) -> int:
        return self._id

    def update(self):
        if self._if_dragging:
            self.handle_mouse()
        self.rect.topleft = self._act_location
        if (
            not pygame.mouse.get_pressed()[0]
            and 150 < math.sqrt(
                (self._act_location[0] - self._map_point[0])**2
                + (self._act_location[1] - self._map_point[1])**2
            )
        ):
            self.validate_move()

    def handle_mouse(self):
        if (
            DataCache.get_value("act_stage") != GameState.BOARD
            or DataCache.get_value("message_board")
        ):
            return
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]
        if mouse_clicked:
            if self.rect.collidepoint(mouse_pos) and not DataCache.get_value("is_dragging"):
                self.is_dragging = True
                DataCache.set_value("is_dragging", self.is_dragging)
                mouse_x, mouse_y = mouse_pos
                self.drag_offset_x = self.rect.x - mouse_x
                self.drag_offset_y = self.rect.y - mouse_y
        else:
            self.is_dragging = False
            DataCache.set_value("is_dragging", self.is_dragging)

        if self.is_dragging:
            mouse_x, mouse_y = mouse_pos
            self._act_location = (mouse_x + self.drag_offset_x, mouse_y + self.drag_offset_y)

    def validate_move(self):
        loc = [self._act_location[0] + 20, self._act_location[1] + 20]
        DataCache.set_value(
            "new_building",
            loc
        )
        pygame.event.post(pygame.event.Event(EventConfig.NEW_BUILDING))

    def update_data(self, new_place):
        self._map_point = new_place
        self._act_location = (self._map_point[0] - 20, self._map_point[1] - 20)
        self.rect.topleft = self._act_location

    @property
    def moving_point(self):
        return (1080, 60, 40, 40)
