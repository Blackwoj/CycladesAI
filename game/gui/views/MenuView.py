import pygame

from ...static.EventConfig import EventConfig
from ..common.Config import Config
from ..components.Button import Button
from .AbstractView import AbstractView


class MenuView(AbstractView):

    def __init__(self, screen, background):
        super().__init__(screen, background)
        self.play_button = self.org_hov((Config.app.assert_dir), [100, 120])

    def render_view(self):
        self.fill_bg()
        self.button = Button(
            self.screen,
            self.play_button,
            pygame.Rect(200, 350, 100, 120),
            self.switch_to_game
        )
        self.build_nav_bar()
        self.button.update()

    def switch_to_game(self):
        pygame.event.post(pygame.event.Event(EventConfig.SHOW_ROLL))
        print("showed_page")
