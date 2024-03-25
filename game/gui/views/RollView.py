from pathlib import Path

import pygame
from pygame import Surface

from ...DataChache import DataCache
from ..common.Config import Config
from ..components.BidRow import BidRow
from .AbstractView import AbstractView
from ...static.EventConfig import EventConfig


class RollView(AbstractView):

    def __init__(self, screen: Surface, background: Path):
        super().__init__(screen, background)

    def render_view(self):
        self.scale_background(self._background)
        self.build_nav_bar()

        picture = pygame.image.load(Config.app.assert_dir / "bid_points" / "priority.png")
        self.screen.blit(
            self.scale_img(picture, [404, 120]),
            pygame.Rect(60, 0, 404, 120))
        if DataCache.get_value("bid_order"):
            for i, player in enumerate(DataCache.get_value("bid_order")):
                player_icon = pygame.image.load(Config.app.players_icons / (player + ".png"))
                self.screen.blit(
                    self.scale_img(player_icon, [50, 50]),
                    pygame.Rect(*Config.locations.players_bid_order[i])
                )
        picture = pygame.image.load(Config.app.assert_dir / "roll_bg_2.png")
        self.screen.blit(
            self.scale_img(picture, [404, 680]),
            Config.locations.roll_background
        )
        self.build_nav_bar()

        board_picture = pygame.image.load(Config.app.assert_dir / "board.png")
        self.screen.blit(
            self.scale_img(board_picture, [736, 800]),
            Config.locations.roll_board_background
        )

        Row1 = BidRow(self.screen, [100, 127], 1)
        Row1.build_row()
        Row2 = BidRow(self.screen, [100, 265], 2)
        Row2.build_row()
        num_of_players = DataCache.get_value("num_of_players")
        if num_of_players > 3:
            Row3 = BidRow(self.screen, [100, 417], 3)
            Row3.build_row()
        if num_of_players > 4:
            Row4 = BidRow(self.screen, [100, 570], 4)
            Row4.build_row()

        self.appollon_row()
        self.draw_heros()
        pygame.display.update()

    def appollon_row(self):
        appollon = pygame.image.load(Config.app.assert_dir / "heros_boards" / "appollon.png")

        rect = pygame.Rect(95, 710, 350, 90)
        pos = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()

        hit = rect.collidepoint(pos)
        if hit and pressed[0] == 1:
            pygame.event.post(pygame.event.Event(EventConfig.APPOLLON_BID))

        self.screen.blit(
            self.scale_img(appollon, [350, 90]),
            rect
        )

        appollon_row_bids = DataCache.get_value("bids_value")["row_5"]
        if appollon_row_bids:
            for i, player in enumerate(appollon_row_bids):
                player_img = pygame.image.load(Config.app.players_icons / f"{player}.png")
                self.screen.blit(
                    self.scale_img(player_img, [35, 35]),
                    Config.locations.appollon_players_locations[i]
                )

    def draw_heros(self):
        for row, hero in DataCache.get_value("heros_per_row").items():
            if hero:
                hero_img = pygame.image.load(Config.app.assert_dir / "heros_boards" / f"{hero}.png")
                self.screen.blit(
                    self.scale_img(hero_img, [340, 100]),
                    Config.locations.heros_board_location[row]
                )
