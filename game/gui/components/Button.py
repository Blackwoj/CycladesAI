from pathlib import Path
from typing import Callable

import pygame


class Button:
    def __init__(
        self,
        screen: pygame.Surface,
        image_path: Path,
        position: pygame.Rect,
        callback: Callable = None,
    ):
        self.screen = screen
        self.callback = callback

        # Load original and hover images, handling potential errors
        self.org_image = None
        self.hov_image = None
        try:
            self.org_image = pygame.image.load(str(image_path / "org.png"))
            self.hov_image = pygame.image.load(str(image_path / "hov.png"))
        except FileNotFoundError as e:
            print(f"Error loading images: {e}")
            return  # Exit initialization if images not found

        # Apply scale factor
        self.org_image = pygame.transform.scale(self.org_image, (position.width, position.height))
        self.hov_image = pygame.transform.scale(self.hov_image, (position.width, position.height))

        # Update rect based on scaled images
        self.rect = self.org_image.get_rect(topleft=position.topleft)

    def update(self):
        pos = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        hit = self.rect.collidepoint(pos)

        if hit:
            self.screen.blit(self.hov_image, self.rect)
        else:
            self.screen.blit(self.org_image, self.rect)

        if hit and click[0] == 1 and self.callback is not None:
            self.callback()  # Call the callback function if defined

