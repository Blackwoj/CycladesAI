import math
from abc import abstractmethod
from typing import Optional, Union

import pygame

from ....DataCache import DataCache
from ....dataclasses.EntitiesDataClass import Entity
from ....dataclasses.IncomeDataClass import Income
from ...common.Config import Config


class AbstractEntity(pygame.sprite.Sprite):

    def __init__(
        self,
        entity_id: int,
        screen: pygame.Surface,
        entity_data: Union[Entity, Income],
        entity_owner: str,
        entity_location: str,
        entity_icon: pygame.Surface,
        multiply_icon: dict[int, pygame.Surface],
        ownership_icon: Optional[pygame.Surface] = None,
    ):
        self._id = entity_id
        self.screen = screen
        self.entity_data = entity_data
        self.entity_owner = entity_owner
        self.entity_location = entity_location
        if not entity_location:
            self._map_point = Config.boards.new_special_event_loc
        else:
            self._map_point = self.entities_map_points(entity_data._type, entity_location)
        self._act_location = (self._map_point[0] - self.icon_size, self._map_point[1] - self.icon_size)
        self._entity_icon = entity_icon
        self._ownership_icon = ownership_icon
        self._multiply_icon = multiply_icon
        self.is_dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        super().__init__()
        self.image = self.get_image()
        self.rect = self.image.get_rect()
        self.rect.topleft = self._act_location

    @staticmethod
    def entities_map_points(_type, location) -> list[int]:
        map_points = {
            "warrior": Config.boards.warriors_points[str(DataCache.get_value("num_of_players"))],
            "ship": Config.boards.circles_centers[str(DataCache.get_value("num_of_players"))],
            "income": Config.boards.income_point[str(DataCache.get_value("num_of_players"))]
        }
        return map_points[_type][location]

    @property
    def entity_id(self) -> int:
        return self._id

    @property
    @abstractmethod
    def icon_size(self) -> int:
        raise NotImplementedError

    def update(self):
        self.handle_mouse()
        self.rect.topleft = self._act_location
        if (
            not pygame.mouse.get_pressed()[0]
            and 70 < math.sqrt(
                (self._act_location[0] + self.icon_size - self._map_point[0])**2
                + (self._act_location[1] + self.icon_size - self._map_point[1])**2
            )
        ):
            self.validate_move()

    def get_image(self):
        if self.entity_data.quantity and self.entity_data.quantity > 0:
            entity_image = self._entity_icon.copy()
            multiply_image = self._multiply_icon[self.entity_data.quantity]
            entity_image.blit(multiply_image, (entity_image.get_width() - multiply_image.get_width(), 0))
        elif self._ownership_icon:
            entity_image = self._ownership_icon.copy()
        else:
            entity_image = pygame.Surface([0, 0])
        return entity_image

    def handle_mouse(self):
        if self.handle_mouse_validator:
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

    @abstractmethod
    def validate_move(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def handle_mouse_validator(self) -> bool:
        raise NotImplementedError

    def update_data(self, new_place, quantity):
        self._map_point = new_place
        self.entity_data.quantity = quantity
        self._act_location = (self._map_point[0] - self.icon_size, self._map_point[1] - self.icon_size)
        self.image = self.get_image()
        self.rect.topleft = self._act_location
