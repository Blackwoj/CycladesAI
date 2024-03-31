import pygame
from ....DataCache import DataCache
from abc import abstractmethod


class AbstractEntity(pygame.sprite.Sprite):

    def __init__(
        self,
        entity_id: int,
        screen: pygame.Surface,
        map_point: list[int],
        num_of_entities: int,
        owner: str,
        entity_icon: pygame.Surface,
        multiply_icon: dict[int, pygame.Surface]
    ):
        self._id = entity_id
        self.screen = screen
        self._map_point = map_point
        self._act_location = (self._map_point[0] - 80 // 2, self._map_point[1] - 80 // 2)
        self._num_of_entities = num_of_entities
        self._owner = owner
        self._entity_icon = entity_icon
        self._multiply_icon = multiply_icon
        self.is_dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        super().__init__()
        self.image = self.get_image()
        self.rect = self.image.get_rect()
        self.rect.topleft = self._act_location

    def update(self):
        self.handle_mouse()
        self.rect.topleft = self._act_location
        if not pygame.mouse.get_pressed()[0] and self._act_location != self._map_point:
            self.validate_move()

    def get_image(self):
        entity_image = self._entity_icon.copy()
        multiply_image = self._multiply_icon[self._num_of_entities]
        entity_image.blit(multiply_image, (entity_image.get_width() - multiply_image.get_width(), 0))
        return entity_image

    def handle_mouse(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]  # Sprawdź, czy lewy przycisk myszy jest wciśnięty

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

    def draw(self):
        self.screen.blit(self.image, self._act_location)

    @abstractmethod
    def validate_move(self):
        raise NotImplementedError
