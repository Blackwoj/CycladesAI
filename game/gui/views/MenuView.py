import pygame

from ..common.Config import Config
from ..components.Button import Button
from .AbstractView import AbstractView
from ...static.EventConfig import EventConfig


class MenuView(AbstractView):

    def __init__(self, screen, background):
        super().__init__(screen, background)

    def render_view(self):
        self.scale_background(self._background)

        img_path = Config.app.assert_dir
        self.button = Button(
            self.screen,
            img_path,
            pygame.Rect(100, 100, 100, 120),
            self.switch_to_game
        )
        self.button.update()

    def switch_to_game(self):
        pygame.event.post(pygame.event.Event(EventConfig.SHOW_ROLL))
        print("showed_page")
