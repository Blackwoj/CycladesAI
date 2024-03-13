from abc import ABC, abstractmethod
from pathlib import Path

import pygame


class AbstractView(ABC):

    def __init__(self, screen: pygame.Surface, background):
        self.screen = screen
        self._background = background

    def scale_background(self, background_file: Path):
        bg = pygame.image.load(background_file)

        scaled_bg = pygame.transform.scale(bg, (self.screen.get_width(), self.screen.get_height()))
        self.screen.blit(scaled_bg, (0, 0))

    @abstractmethod
    def render_view(self):
        raise NotImplementedError
