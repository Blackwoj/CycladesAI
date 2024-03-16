from pygame import Surface
import pygame
from .AbstractView import AbstractView
from ..common.Config import Config
from pathlib import Path
from ..components.BidRow import BidRow
from .

class RollView(AbstractView):

    def __init__(self, screen: Surface, background: Path):
        super().__init__(screen, background)

    def render_view(self):
        self.scale_background(self._background)

        picture = pygame.image.load(Config.app.assert_dir / "bid_points" / "priority.png")
        self.screen.blit(
            self.scale_img(picture, [404, 120]),
            pygame.Rect(60, 0, 404, 120))
        self.build_nav_bar()
        picture = pygame.image.load(Config.app.assert_dir / "roll_bg_2.png")
        self.screen.blit(
            self.scale_img(picture, [404, 680]),
            pygame.Rect(60, 120, 404, 800))
        self.build_nav_bar()

        board_picture = pygame.image.load(Config.app.assert_dir / "board.png")
        self.screen.blit(
            self.scale_img(board_picture, [736, 800]),
            pygame.Rect(464, 0, 736, 800)
        )
        Row1 = BidRow(self.screen, [100, 127], 1)
        Row1.build_row()
        Row2 = BidRow(self.screen, [100, 265], 2)
        Row2.build_row()
        Row3 = BidRow(self.screen, [100, 417], 3)
        Row3.build_row()
        Row4 = BidRow(self.screen, [100, 570], 4)
        Row4.build_row()
        pygame.display.update()
