from abc import ABC, abstractmethod
from pathlib import Path

import pygame
from ..components.Button import Button
from ..common.Config import Config
from ...DataChache import DataCache


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

        hero_player_name = str(DataCache.get_value("hero_players")[DataCache.get_value("act_player")])+".png"
        hero_icon = pygame.image.load(Config.app.nav_bar / "hero" / hero_player_name)
        self.screen.blit(self.scale_img(hero_icon, [60, 60]), [0, 500])

        philosophers_player_name = str(DataCache.get_value("philosophers")[DataCache.get_value("act_player")])+".png"
        philosophers_icon = pygame.image.load(Config.app.nav_bar / "philosophers" / philosophers_player_name)
        self.screen.blit(self.scale_img(philosophers_icon, [60, 60]), [0, 560])

        priests_player_name = str(DataCache.get_value("priests")[DataCache.get_value("act_player")])+".png"
        priests_icon = pygame.image.load(Config.app.nav_bar / "priests" / priests_player_name)
        self.screen.blit(self.scale_img(priests_icon, [60, 60]), [0, 620])

        coin_player_name = str(DataCache.get_value("coins")[DataCache.get_value("act_player")])+".png"
        coin_icon = pygame.image.load(Config.app.nav_bar / "coins" / coin_player_name)
        self.screen.blit(self.scale_img(coin_icon, [60, 60]), [0, 680])
        player_icon = pygame.image.load(Config.app.nav_bar / "player_marks" / (DataCache.get_value("act_player")+".png"))
        self.screen.blit(self.scale_img(player_icon, [60, 60]), [0, 740])

        board_button.update()
        roll_button.update()
        setting_button.update()
        self.screen.blit(self.scale_img(game_icon, [60.0, 60.0]), (0, 0))

    def scale_img(self, image: pygame.Surface, size: list[float]) -> pygame.Surface:
        return pygame.transform.scale(image, size)

    def clicked(self):
        print("Clicked!")

    @abstractmethod
    def render_view(self):
        raise NotImplementedError
