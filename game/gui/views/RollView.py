from pathlib import Path

import pygame
from pygame import Surface

from ...DataCache import DataCache
from ...static.EventConfig import EventConfig
from ..common.Config import Config
from ..components.BidRow import BidRow
from .AbstractView import AbstractView


class RollView(AbstractView):

    def __init__(self, screen: Surface, background: Path):
        super().__init__(screen, background)
        self.pull_img()

    def pull_img(self):
        self.priority_img = self.load_and_scale(
            (Config.app.bid_icon_dir / "priority.png"),
            [404, 120]
        )
        self.roll_img = self.load_and_scale((Config.app.assert_dir / "roll_bg_2.png"), [404, 680])
        self.heros_imgs = {
            _hero: self.load_and_scale((Config.app.heros_plates / f"{_hero}.png"), [335, 95])
            for _hero in ["ares", "posejdon", "atena", "zeus"]
        }
        self.board_pictures = {
            str(i): self.load_and_scale((Config.app.boards_path / f"{i}.png"), [736, 800])
            for i in range(2, 6)
        }
        self.players_icons_27 = {
            _player: self.load_and_scale((Config.app.players_icons / f"{_player}.png"), [27, 27])
            for _player in ["p1", "p2", "p3", "p4", "p5"]
        }
        self.players_icons_50 = {
            _player: self.load_and_scale((Config.app.players_icons / f"{_player}.png"), [50, 50])
            for _player in ["p1", "p2", "p3", "p4", "p5"]
        }
        self.bids = {
            str(i): self.load_and_scale((Config.app.bid_icon_dir / f"{i}.png"), [27, 27])
            for i in range(1, 11)
        }

    def render_view(self):
        self.fill_bg()
        self.build_nav_bar()

        self.screen.blit(
            self.priority_img,
            pygame.Rect(60, 0, 404, 120))
        if DataCache.get_value("bid_order"):
            for i, player in enumerate(DataCache.get_value("bid_order")):
                self.screen.blit(
                    self.players_icons_50[str(player)],
                    pygame.Rect(*Config.locations.players_bid_order[i])
                )
        self.screen.blit(
            self.roll_img,
            Config.locations.roll_background
        )
        self.build_nav_bar()

        num_of_players = DataCache.get_value("num_of_players")
        self.screen.blit(
            self.board_pictures[str(num_of_players)],
            Config.locations.roll_board_background
        )

        Row1 = BidRow(self.screen, [92, 130], 1, self.bids, self.players_icons_27)
        Row1.build_row()
        Row2 = BidRow(self.screen, [92, 270], 2, self.bids, self.players_icons_27)
        Row2.build_row()
        num_of_players = DataCache.get_value("num_of_players")
        if num_of_players > 3:
            Row3 = BidRow(self.screen, [92, 410], 3, self.bids, self.players_icons_27)
            Row3.build_row()
        if num_of_players > 4:
            Row4 = BidRow(self.screen, [92, 550], 4, self.bids, self.players_icons_27)
            Row4.build_row()

        self.appollon_row()
        self.draw_heros()
        pygame.display.update()

    def appollon_row(self):
        rect = pygame.Rect(95, 690, 335, 90)
        pos = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()

        hit = rect.collidepoint(pos)
        if hit and pressed[0] == 1:
            pygame.event.post(pygame.event.Event(EventConfig.APPOLLON_BID))

        appollon_row_bids = DataCache.get_value("bids_value")["row_5"]
        if appollon_row_bids:
            for i, player in enumerate(appollon_row_bids):
                self.screen.blit(
                    self.players_icons_27[player],
                    Config.locations.appollon_players_locations[i]
                )

    def draw_heros(self):
        for row, hero in DataCache.get_value("heros_per_row").items():
            if hero:
                self.screen.blit(
                    self.heros_imgs[hero],
                    Config.locations.heros_board_location[row]
                )
