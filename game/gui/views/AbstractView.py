from abc import ABC, abstractmethod
from pathlib import Path

import pygame
from ..components.Button import Button
from ..common.Config import Config
class AbstractView(ABC):

    def __init__(self, screen: pygame.Surface, background: Path):
        self.screen = screen
        self._background = background

    def scale_background(self, background_file: Path):
        bg = pygame.image.load(background_file)

        scaled_bg = pygame.transform.scale(bg, (self.screen.get_width(), self.screen.get_height()))
        self.screen.blit(scaled_bg, (0, 0))

    def build_nav_bar(self):
        game_icon = pygame.image.load(Config.app.nav_bar / "gameIcon.png")
        board_button = Button(
            self.screen,
            Config.app.nav_bar / "board",
            pygame.Rect(0, 60, 60, 60),
            self.clicked
        )
        roll_button = Button(
            self.screen,
            Config.app.nav_bar / "roll",
            pygame.Rect(0, 120, 60, 60),
            self.clicked
        )
        setting_button = Button(
            self.screen,
            Config.app.nav_bar / "settings",
            pygame.Rect(0, 180, 60, 60),
            self.clicked
        )
        board_button.update()
        roll_button.update()
        setting_button.update()
        self.screen.blit(self.scale_img(game_icon, [60.0, 60.0]), (0, 0))

    def scale_img(self, image: pygame.Surface, size: list[float]) -> pygame.Surface:
        return pygame.transform.scale(image, size)

    def clicked(sefl):
        print("Clicked!")

    @abstractmethod
    def render_view(self):
        raise NotImplementedError
