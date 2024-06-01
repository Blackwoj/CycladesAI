import time
from pathlib import Path
from typing import Callable

import pygame

from ...DataCache import DataCache
from ...enums.GameState import GameState
from ..common.Config import Config
from ..components.Button import Button
from ..components.entities.BuildingEntity import BuildingEntity
from ..components.entities.WarriorEntity import WarriorEntity
from ..components.entities.ShipEntity import ShipEntity
from ..components.entities.IncomeEntity import IncomeEntity
from ..components.MessageBoxes.WarriorMessageBox import WarriorMessageBox
from ..components.MessageBoxes.ShipMessageBox import ShipMessageBox
from .AbstractView import AbstractView


class BoardView(AbstractView):

    def __init__(self, screen: pygame.Surface, background: Path):
        super().__init__(screen, background)
        self.entities_sprite = pygame.sprite.Group()
        self.building_sprite = pygame.sprite.Group()
        self.income_sprite = pygame.sprite.Group()
        self.message_box = {
            "warrior": WarriorMessageBox(self.screen),
            "ship": ShipMessageBox(self.screen)
        }
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
        self.ownership_icon = {
            _player: self.load_and_scale((Config.app.boards_items / "ownership" / f"{_player}.png"), [80, 80])
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
        self._buildings = {
            building: self.load_and_scale((Config.app.building_icons / f"{building}.png"), [40, 40])
            for building in ["atena", "ares", "posejdon", "zeus", "metro"]
        }
        self._income_icon = self.load_and_scale((Config.app.boards_items / "rog.png"), [40, 40])

    def update_sprite(self):
        self.load_warriors()
        self.entities_sprite.update()
        if (
            DataCache.get_value("new_player")
            and DataCache.get_value("act_stage") == GameState.BOARD
            and DataCache.get_value("act_hero")
        ):
            self.load_hero_layout()
            DataCache.set_value("new_player", False)
        self.building_sprite.update()
        self.income_sprite.update()
        self.income_sprite.draw(self.screen)
        self.building_sprite.draw(self.screen)
        self.entities_sprite.draw(self.screen)

    def render_view(self):
        self.fill_bg()
        self.build_nav_bar()
        self.screen.blit(self._boards[str(DataCache.get_value("num_of_players"))], [60, 0])
        self.screen.blit(self._play_order, [1140, 0])
        self.load_warriors()
        self.update_entity()
        self.delete_entity()
        self.add_building()
        self.update_sprite()
        self.load_ships()
        # self.load_items()
        # self.load_buildings()
        self.build_message_box()
        self.load_income()
        if DataCache.get_value("act_stage") == GameState.BOARD:
            self.next_player_button()
        self.draw_all_points()

    def build_message_box(self):
        message = DataCache.get_value("message_board")
        if message:
            self.message_box[message["property"]].build_box(message["msg"])

    def load_items(self):
        _circle_centers = Config.boards.circles_centers
        for _, location in _circle_centers[str(DataCache.get_value("num_of_players"))].items():
            if location:
                self.draw_center(self.screen, (255, 0, 0), location, 10)

    def draw_all_points(self):
        water = Config.boards.circles_centers[str(DataCache.get_value("num_of_players"))]
        for key, loc in water.items():
            self.draw_center(self.screen, "red", loc, 5)

    def draw_center(self, screen, color, center, radius):
        pygame.draw.circle(screen, color, tuple(center), radius)

    def load_warriors(self):
        _warriors_points = Config.boards.warriors_points[str(DataCache.get_value("num_of_players"))]
        for _warrior_id, warrior_stats in DataCache.get_value("warriors_status").items():
            if _warrior_id in self._loaded_entities:
                continue
            self._loaded_entities.append(_warrior_id)
            warrior_entity = WarriorEntity(
                _warrior_id,
                self.screen,
                _warriors_points[warrior_stats["field"]],
                warrior_stats["num_of_entities"],
                warrior_stats["owner"],
                self._warriors_icon[warrior_stats["owner"]],
                self.ownership_icon[warrior_stats["owner"]],
                self._multiplayer_icon
            )
            self.entities_sprite.add(warrior_entity)

    def update_entity(self):
        _entity_to_update = DataCache.get_value("entity_update")
        if not _entity_to_update:
            return
        for sprite_group in [self.entities_sprite, self.income_sprite]:
            for entity in sprite_group:
                if entity.entity_id in _entity_to_update.keys():
                    entity.update_data(
                        _entity_to_update[entity.entity_id]["location"],
                        _entity_to_update[entity.entity_id]["num_of_entities"]
                    )
        DataCache.set_value("entity_update", {})

    def delete_entity(self):
        delete_entity = DataCache.get_value("entity_delete")
        if not delete_entity:
            return
        for sprite_group in [self.entities_sprite, self.income_sprite]:
            for entity in sprite_group:
                if entity.entity_id in delete_entity:
                    sprite_group.remove(entity)
        DataCache.set_value("entity_delete", [])

    def load_ships(self):
        _warriors_points = Config.boards.warriors_points[str(DataCache.get_value("num_of_players"))]
        for _warrior_id, warrior_stats in DataCache.get_value("warriors_status").items():
            if _warrior_id in self._loaded_entities:
                continue
            self._loaded_entities.append(_warrior_id)
            warrior_entity = WarriorEntity(
                _warrior_id,
                self.screen,
                _warriors_points[warrior_stats["field"]],
                warrior_stats["num_of_entities"],
                warrior_stats["owner"],
                self._warriors_icon[warrior_stats["owner"]],
                self.ownership_icon[warrior_stats["owner"]],
                self._multiplayer_icon
            )
            self.entities_sprite.add(warrior_entity)
        _ships_points = Config.boards.circles_centers[str(DataCache.get_value("num_of_players"))]
        for _ship_id, ship_stats in DataCache.get_value("ship_status").items():
            if _ship_id in self._loaded_entities:
                continue
            self._loaded_entities.append(_ship_id)
            ship_entity = ShipEntity(
                _ship_id,
                self.screen,
                _ships_points[ship_stats["field"]],
                ship_stats["num_of_entities"],
                ship_stats["owner"],
                self._ships_icon[ship_stats["owner"]],
                self.ownership_icon[ship_stats["owner"]],
                self._multiplayer_icon
            )
            self.entities_sprite.add(ship_entity)

    def load_income(self):
        _income_points = Config.boards.income_point[str(DataCache.get_value("num_of_players"))]
        income_status = DataCache.get_value("income_status")
        for id, income_config in income_status.items():
            if id in self._loaded_entities:
                continue
            self._loaded_entities.append(id)
            income_entity = IncomeEntity(
                id,
                self.screen,
                _income_points[income_config["location"]],
                income_config["num_of_entities"],
                self._income_icon,
                self._multiplayer_icon,
                allow_drag=False
            )
            self.income_sprite.add(income_entity)

    def load_buildings(self):
        _buildings_centers = Config.boards.buildings_centers
        for _, buildings in _buildings_centers[str(DataCache.get_value("num_of_players"))].items():
            small_buildings = buildings["small"]
            big_buildings = buildings["big"]
            if small_buildings:
                for location in small_buildings:
                    if location:
                        self.draw_center(self.screen, (0, 255, 0), location, 3)
            if big_buildings:
                self.draw_center(self.screen, (0, 0, 255), big_buildings, 3)

    def add_building(self):
        buildings = DataCache.get_value("buildings_status")
        _if_new = False
        for building_id in buildings.keys():
            if building_id and building_id not in self._loaded_entities:
                building = BuildingEntity(
                    building_id,
                    self.screen,
                    buildings[building_id]["loc"],
                    self._buildings[buildings[building_id]["hero"]],
                    False
                )
                self.building_sprite.add(building)
                self._loaded_entities.append(building_id)
                _if_new = True
        if _if_new:
            for building in self.building_sprite:
                if building._id == 1:
                    self.building_sprite.remove(building)
            self.load_hero_layout()
        elif DataCache.get_value("reset_building"):
            DataCache.set_value("reset_building", False)
            for building in self.building_sprite:
                if building._id == 1:
                    self.building_sprite.remove(building)
            self.load_hero_layout()

    def load_hero_layout(self):
        if DataCache.get_value("act_hero"):
            self.heros_layout[DataCache.get_value("act_hero")]()

    def load_ares(self):
        base_building = BuildingEntity(
            1,
            self.screen,
            [1100, 80],
            self._buildings["ares"],
            True
        )
        self.building_sprite.add(base_building)

    def load_poseidon(self):
        base_building = BuildingEntity(
            1,
            self.screen,
            [1100, 80],
            self._buildings["posejdon"],
            True
        )
        self.building_sprite.add(base_building)
        print("load_posejdon")

    def load_athena(self):
        base_building = BuildingEntity(
            1,
            self.screen,
            [1100, 80],
            self._buildings["atena"],
            True
        )
        self.building_sprite.add(base_building)
        print("loading atena")

    def load_zeus(self):
        base_building = BuildingEntity(
            1,
            self.screen,
            [1100, 80],
            self._buildings["zeus"],
            True
        )
        self.building_sprite.add(base_building)
        print("loading zeus")

    def load_appollon(self):
        base_income = IncomeEntity(
            1,
            self.screen,
            [1100, 80],
            1,
            self._income_icon,
            self._multiplayer_icon,
            True
        )
        self.income_sprite.add(base_income)
        print("loading apollon", DataCache.get_value("act_hero"))

    def next_player_button(self):
        next_player_button = Button(
            self.screen,
            self.board_icon,
            pygame.Rect(1080, 0, 60, 60),
            self.clear_player
        )
        next_player_button.update()

    def clear_player(self):
        DataCache.set_value("act_player", "")
        for sprite in self.building_sprite:
            if sprite._id == 1:
                self.building_sprite.remove(sprite)
        DataCache.set_value("new_player", True)
        time.sleep(0.5)

    @property
    def heros_layout(self) -> dict[str, Callable]:
        heros = {
            "apollon": self.load_appollon,
            "zeus": self.load_zeus,
            "atena": self.load_athena,
            "posejdon": self.load_poseidon,
            "ares": self.load_ares,
            "ap_s": self.load_appollon
        }
        return heros
