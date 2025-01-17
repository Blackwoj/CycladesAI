from typing import Callable, Optional

import pygame

from ...DataCache import DataCache


class Button:
    def __init__(
        self,
        screen: pygame.Surface,
        imagines: dict[str, pygame.Surface],
        position: pygame.Rect,
        callback: Optional[Callable] = None,
    ):
        self.screen = screen
        self.callback = callback
        self.icons = imagines

        self.rect = self.icons["org"].get_rect(topleft=position.topleft)

    def update(self):
        pos = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        hit = self.rect.collidepoint(pos)

        if hit and not DataCache.get_value("is_dragging"):
            self.screen.blit(self.icons["hov"], self.rect)
        else:
            self.screen.blit(self.icons["org"], self.rect)

        if hit and click[0] == 1 and self.callback is not None and not DataCache.get_value("is_dragging"):
            self.callback()
