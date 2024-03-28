from pathlib import Path

import pygame

from .AbstractView import AbstractView
from ..common.Config import Config
from ...DataChache import DataCache

class BoardView(AbstractView):

    def __init__(self, screen: pygame.Surface, background: Path):
        super().__init__(screen, background)

    def render_view(self):
        pass
        # self.scale_background(self._background)
        # self.build_nav_bar()
        # _board_file_name = str(DataCache.get_value("num_of_players")) + ".png"
        # _board_page = pygame.image.load(Config.app.boards / _board_file_name)
        # self.screen.blit(self.scale_img(_board_page, [1140, 800]), [60, 0])
