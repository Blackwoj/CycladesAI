from pathlib import Path
from typing import Callable, Optional

import pygame

import logging


class Button:
    def __init__(
        self,
        screen: pygame.Surface,
        image_path: Path,
        position: pygame.Rect,
        callback: Optional[Callable] = None,
    ):
        self.screen = screen
        self.callback = callback

        self.org_image = None
        self.hov_image = None
        try:
            self.org_image = pygame.image.load(str(image_path / "org.png"))
            self.hov_image = pygame.image.load(str(image_path / "hov.png"))
        except FileNotFoundError as e:
            logging.warning(f"Error loading images: {e}")
            return

        self.org_image = pygame.transform.scale(self.org_image, (position.width, position.height))
        self.hov_image = pygame.transform.scale(self.hov_image, (position.width, position.height))

        self.rect = self.org_image.get_rect(topleft=position.topleft)

    def update(self):
        pos = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        hit = self.rect.collidepoint(pos)

        if hit and self.hov_image:
            self.screen.blit(self.hov_image, self.rect)
        elif self.org_image:
            self.screen.blit(self.org_image, self.rect)

        if hit and click[0] == 1 and self.callback is not None:
            self.callback()
