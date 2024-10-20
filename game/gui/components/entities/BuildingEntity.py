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
        entity_icons: list[pygame.Surface],
        if_dragging: bool,
        champion: str,
        island: str = ""
    ):
        self._id = entity_id
        self.screen = screen
        self._map_point = map_point
        self._shift = 20 if champion == "metro" else 20
        self._act_location = (self._map_point[0] - self._shift, self._map_point[1] - self._shift)
        self._if_dragging = if_dragging
        self.is_dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        super().__init__()
        self._act_img = 0
        self._entity_icons = entity_icons
        self.image = self._entity_icons[self._act_img]
        self.rect = self.image.get_rect()
        self.rect.topleft = self._act_location
        self.already_clicked = False
        self._champion = champion
        self._island = island

    @property
    def entity_id(self) -> int:
        return self._id

    def update(self):
        if self._if_dragging:
            self.handle_mouse()
        elif DataCache.get_value("metro_building") and self._champion != "metro":
            self._handle_build_delete()
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
            or DataCache.get_value("metro_building")
            and self._champion != "metro"
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

    def _handle_build_delete(self):
        if (
            DataCache.get_value("act_stage") != GameState.BOARD
            or DataCache.get_value("message_board")
            or DataCache.get_value("is_dragging")
        ):
            return
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]
        self._reset_status_clicked()
        if mouse_clicked:
            if self.validate_click(mouse_pos):
                _selected_buildings = DataCache.get_value("building_to_delete")
                self._act_img = 1 if self._act_img == 0 else 0
                _selected_buildings[self._champion] = self._id if self._act_img else -1
                self.already_clicked = True
                self.image = self._entity_icons[self._act_img]
                DataCache.set_value("building_to_delete", _selected_buildings)
        else:
            self.already_clicked = False

    def validate_click(self, mouse_pos):
        _act_player = DataCache.get_value("act_player")
        _selected_buildings = DataCache.get_value("building_to_delete")
        _filed_status = DataCache.get_value("fields_status")
        return (
            _filed_status[self._island].owner == _act_player
            and not self.already_clicked
            and self.rect.collidepoint(mouse_pos)
            and (
                self._champion not in _selected_buildings.keys()
                or _selected_buildings[self._champion] == self._id
                or _selected_buildings[self._champion] == -1
            )
        )

    def _reset_status_clicked(self):
        _act_player = DataCache.get_value("act_player")
        _selected_buildings = DataCache.get_value("building_to_delete")
        _field_status = DataCache.get_value("fields_status")
        if _field_status[self._island].owner != _act_player and self._act_img == 1:
            self._act_img = 0
            if self._champion in _selected_buildings.keys() and _selected_buildings[self._champion] == self._id:
                _selected_buildings[self._champion] = -1
            self.already_clicked = False
            self.image = self._entity_icons[self._act_img]
        DataCache.set_value("building_to_delete", _selected_buildings)

    def validate_move(self):
        loc = [self._act_location[0] + self._shift, self._act_location[1] + self._shift]
        DataCache.set_value(
            "new_building",
            loc
        )
        pygame.event.post(pygame.event.Event(EventConfig.NEW_BUILDING))

    def update_data(self, new_place):
        self._map_point = new_place
        self._act_location = (self._map_point[0] - self._shift, self._map_point[1] - self._shift)
        self.rect.topleft = self._act_location

    @property
    def moving_point(self):
        return (1080, 60, 40, 40)
