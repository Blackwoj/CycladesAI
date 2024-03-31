from pathlib import Path
from ..components.entities.WarriorEnitity import WarriorEntity
import pygame

from ...DataCache import DataCache
from ..common.Config import Config
from .AbstractView import AbstractView


class BoardView(AbstractView):

    def __init__(self, screen: pygame.Surface, background: Path):
        super().__init__(screen, background)
        self.entities_sprite = pygame.sprite.Group()
        self._loaded_entities = []
        self.pull_img()

    def pull_img(self):
        self._boards = {
            str(i): self.load_and_scale((Config.app.boards_path / f"{i}.png"), [1140, 800])
            for i in range(2, 6)
        }
        self._player_icon_20 = {
            _player: self.load_and_scale((Config.app.players_icons / f"{_player}.png"), [20, 20])
            for _player in ["p1", "p2", "p3", "p4", "p5"]
        }
        self._warriors_icon = {
            _player: self.load_and_scale((Config.app.boards_items / "wariors" / f"{_player}.png"), [80, 80])
            for _player in ["p1", "p2", "p3", "p4", "p5"]
        }
        self._ships_icon = {
            _player: self.load_and_scale((Config.app.boards_items / "ships" / f"{_player}.png"), [80, 80])
            for _player in ["p1", "p2", "p3", "p4", "p5"]
        }
        self._multiplayer_icon = {
            i: self.load_and_scale((Config.app.boards_items / "multiplier" / f"{i}.png"), [30, 30])
            for i in range(1, 7)
        }
        self._play_order = self.load_and_scale((Config.app.boards_items / "order.png"), [60, 250])

    def update_sprite(self):
        self.load_warriors()
        self.entities_sprite.update()
        # print(self.entities_sprite)
        self.entities_sprite.draw(self.screen)

    def render_view(self):
        self.fill_bg()
        self.build_nav_bar()
        self.screen.blit(self._boards[str(DataCache.get_value("num_of_players"))], [60, 0])
        self.screen.blit(self._play_order, [1140, 0])
        self.update_sprite()
        self.load_ships()
        # self.load_items()
        # self.load_buildings()
        self.load_warriors()
        # self.load_income()

    def load_items(self):
        _circle_centers = Config.boards.circles_centers
        for center, location in _circle_centers[str(DataCache.get_value("num_of_players"))].items():
            if location:
                self.draw_center(self.screen, (255, 0, 0), location, 10)

    def draw_center(self, screen, color, center, radius):
        pygame.draw.circle(screen, color, tuple(center), radius)

    def load_warriors(self):
        _warriors_points = Config.boards.warriors_points[str(DataCache.get_value("num_of_players"))]
        for _warrior_id, warrior_stats in DataCache.get_value("warriors_status").items():
            if _warrior_id in self._loaded_entities:
                continue
            print(_warrior_id, warrior_stats)
            self._loaded_entities.append(_warrior_id)
            warrior_entity = WarriorEntity(
                _warrior_id,
                self.screen,
                _warriors_points[warrior_stats["island"]],
                warrior_stats["num_of_entities"],
                warrior_stats["owner"],
                self._warriors_icon[warrior_stats["owner"]],
                self._multiplayer_icon
            )
            self.entities_sprite.add(warrior_entity)

    def load_ships(self):
        _ships_points = Config.boards.circles_centers[str(DataCache.get_value("num_of_players"))]
        for water_point, values_for_island in DataCache.get_value("water_status").items():
            x = _ships_points[water_point][0] - 80 // 2
            y = _ships_points[water_point][1] - 80 // 2
            self.screen.blit(self._ships_icon[values_for_island["owner"]], (x, y))
            self.screen.blit(
                self._multiplayer_icon[values_for_island["num_of_entities"]],
                (x + 40, y)
            )

    def load_income(self):
        _income_points = Config.boards.income_point
        for island, location in _income_points[str(DataCache.get_value("num_of_players"))].items():
            if location:
                self.draw_center(self.screen, (255, 255, 255), location, 3)
        pass

    def load_buildings(self):
        _buildings_cneters = Config.boards.buildings_centers
        for islands, buildings in _buildings_cneters[str(DataCache.get_value("num_of_players"))].items():
            small_buildings = buildings["small"]
            big_buildings = buildings["big"]
            if small_buildings:
                for location in small_buildings:
                    if location:
                        self.draw_center(self.screen, (0, 255, 0), location, 3)
            if big_buildings:
                self.draw_center(self.screen, (0, 0, 255), big_buildings, 3)
        pass
