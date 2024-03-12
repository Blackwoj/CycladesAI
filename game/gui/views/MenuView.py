from .AbstractView import AbstractView
from ..common.Config import Config
from ..components.Button import Button
import pygame


class MenuView(AbstractView):

    def __init__(self, screen, background):
        super().__init__(screen, background)

    def render_view(self):
        self.scale_background(self._background/"menu_bg.png")

        img_path = Config.app.assert_dir
        self.button = Button(
            self.screen,
            img_path,
            pygame.Rect(100, 100, 200, 200),
            self.switch_to_game
        )
        self.button.update()

    def switch_to_game(self):
        pass
