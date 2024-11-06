from abc import ABC, abstractmethod
from pathlib import Path

import pygame

from ...DataCache import DataCache
from ...dataclasses.BuildingDataClass import Building
from ...static.EventConfig import EventConfig
from ..common.Config import Config
from ..components.Button import Button


class AbstractView(ABC):

    def __init__(self, screen: pygame.Surface, background: Path):
        self.screen = screen
        self.bg = self.scale_bg(background)
        self.pull_nav_bar()

    def pull_nav_bar(self):
        self.game_icon = self.load_and_scale((Config.app.nav_bar / "gameIcon.png"), [60, 60])
        self.board_icon = self.org_hov((Config.app.nav_bar / "board"), [60, 60])
        self.priest_card = self.load_and_scale((Config.app.boards_items / "priest_card.png"), [60, 100])
        self.philosophers_card = self.load_and_scale((Config.app.boards_items / "phil_card.png"), [60, 100])
        self.roll_icon = self.org_hov((Config.app.nav_bar / "roll"), [60, 60])
        self.settings_icon = self.org_hov((Config.app.nav_bar / "settings"), [60, 60])
        self.priest_icon = {
            str(i): self.load_and_scale((Config.app.nav_bar / "priests" / f"{i}.png"), [60, 60])
            for i in range(0, 11)
        }
        self.coins_icon = {
            str(i): self.load_and_scale((Config.app.nav_bar / "coins" / f"{i}.png"), [60, 60])
            for i in range(0, 30)
        }
        self.philosophers = {
            str(i): self.load_and_scale((Config.app.nav_bar / "philosophers" / f"{i}.png"), [60, 60])
            for i in range(0, 11)
        }
        self.player_icon = {
            _player: self.load_and_scale((Config.app.players_icons / f"{_player}.png"), [60, 60])
            for _player in ["p1", "p2", "p3", "p4", "p5"]
        }
        self.hero_icon = {
            _hero: self.load_and_scale((Config.app.nav_bar / "hero" / f"{_hero}.png"), [60, 60])
            for _hero in ["ares", "posejdon", "atena", "zeus", "None", "apollon", "ap_s"]
        }

    def org_hov(self, img_path: Path, size):
        return {
            "org": self.load_and_scale((img_path / "org.png"), size),
            "hov": self.load_and_scale((img_path / "hov.png"), size),
        }

    def load_and_scale(self, location, size):
        img = pygame.image.load(location).convert_alpha()
        return self.scale_img(img, size)

    def scale_bg(self, bg_path: Path):
        _bg = pygame.image.load(bg_path).convert()
        self._bg = pygame.transform.scale(_bg, (self.screen.get_width(), self.screen.get_height()))

    def fill_bg(self):
        self.screen.blit(self._bg, (0, 0))

    def build_nav_bar(self):
        game_icon = pygame.image.load(Config.app.nav_bar / "gameIcon.png").convert()
        board_button = Button(
            self.screen,
            self.board_icon,
            pygame.Rect(0, 60, 60, 60),
            self.switch_to_board
        )
        roll_button = Button(
            self.screen,
            self.roll_icon,
            pygame.Rect(0, 120, 60, 60),
            self.switch_to_roll
        )
        setting_button = Button(
            self.screen,
            self.settings_icon,
            pygame.Rect(0, 180, 60, 60),
            self.switch_to_menu
        )
        if DataCache.get_value("act_player"):
            hero_player_name = str(
                DataCache.get_value("hero_players")[DataCache.get_value("act_player")]
            )
            self.screen.blit(self.hero_icon[hero_player_name], [0, 500])

            philosophers_player_name = str(
                DataCache.get_value("player_data")[DataCache.get_value("act_player")].philosophers
            )
            self.screen.blit(self.philosophers[philosophers_player_name], [0, 560])

            priests_player_name = str(
                DataCache.get_value("player_data")[DataCache.get_value("act_player")].priests
            )
            self.screen.blit(self.priest_icon[str(priests_player_name)], [0, 620])

            coin_player_name = str(
                DataCache.get_value("player_data")[DataCache.get_value("act_player")].coins
            )
            self.screen.blit(self.coins_icon[str(coin_player_name)], [0, 680])

            self.screen.blit(self.player_icon[DataCache.get_value("act_player")], [0, 740])

        board_button.update()
        roll_button.update()
        setting_button.update()
        self.screen.blit(self.scale_img(game_icon, [60.0, 60.0]), (0, 0))

    def scale_img(self, image: pygame.Surface, size: list[float]) -> pygame.Surface:
        return pygame.transform.scale(image, size)

    def switch_to_roll(self):
        pygame.event.post(pygame.event.Event(EventConfig.SHOW_ROLL))

    def switch_to_board(self):
        pygame.event.post(pygame.event.Event(EventConfig.SHOW_BOARD))

    def switch_to_menu(self):
        filed_config = Config.boards.buildings_centers["5"]
        fields_status = DataCache.get_value("fields_status")
        fields_status["IS13"].buildings["1"] = Building(
            1111,
            'ares',
            filed_config["IS12"]["small"][0],
        )
        fields_status["IS13"].buildings["2"] = Building(
            1112,
            'atena',
            filed_config["IS12"]["small"][1],
        )
        fields_status["IS13"].buildings["3"] = Building(
            1113,
            'posejdon',
            filed_config["IS12"]["small"][2],
        )
        fields_status["IS4"].buildings["2"] = Building(
            1114,
            'zeus',
            filed_config["IS12"]["small"][1],
        )
        DataCache.set_value("fields_status", fields_status)

    @abstractmethod
    def render_view(self):
        raise NotImplementedError
