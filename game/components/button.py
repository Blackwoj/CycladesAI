from pathlib import Path
from typing import Callable

import pygame


class Button:
    def __init__(
        self,
        screen: pygame.Surface,
        image_path: Path,
        position: pygame.Rect,
        callback: Callable):
        self.screen = screen
        self.callback = callback

        self.org_image = pygame.image.load(str(image_path / "org.png"))
        self.hov_image = pygame.image.load(str(image_path / "hov.png"))

        self.rect = self.org_image.get_rect(topleft=position.topleft)

    def update(self):
        pos = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        hit = self.rect.collidepoint(pos)

        if hit:
            self.screen.blit(self.hov_image, self.rect)
        else:
            self.screen.blit(self.org_image, self.rect)

        if hit and click[0] == 1:
            self.callback()
