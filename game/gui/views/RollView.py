from pygame import Surface
import pygame
from .AbstractView import AbstractView
from ..common.Config import Config
from pathlib import Path

class RollView(AbstractView):

    def __init__(self, screen: Surface, background: Path):
        super().__init__(screen, background)

    def render_view(self):
        self.scale_background(self._background)
        picture = pygame.image.load(Config.app.assert_dir / "roll_bg.png")
        scalled_picture = pygame.transform.scale(picture, (404, 800))
        self.screen.blit(
            self.scale_img(picture, [404, 800]),
            pygame.Rect(60, 0, scalled_picture.get_width(), scalled_picture.get_height()))
        self.build_nav_bar()
        board_picture = pygame.image.load(Config.app.assert_dir / "board.png")
        self.screen.blit(
            self.scale_img(board_picture, [736, 800]),
            pygame.Rect(464, 0, board_picture.get_width(), board_picture.get_height())
        )
        pygame.display.update()
