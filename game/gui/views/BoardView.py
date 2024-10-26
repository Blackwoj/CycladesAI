import logging
import time
from pathlib import Path
from typing import Any, Callable

import pygame

from ...DataCache import DataCache
from ...dataclasses.EntitiesDataClass import Entity
from ...dataclasses.FieldDataClass import Fieldv2
from ...dataclasses.IncomeDataClass import Income
from ...dataclasses.BuildingDataClass import Building
from ...enums.GameState import GameState
from ...static.EventConfig import EventConfig
from ..common.Config import Config
from ..components.Button import Button
from ..components.entities.BuildingEntity import BuildingEntity
from ..components.entities.IncomeEntity import IncomeEntity
from ..components.entities.ShipEntity import ShipEntity
from ..components.entities.WarriorEntity import WarriorEntity
from ..components.MessageBoxes.ShipMessageBox import ShipMessageBox
from ..components.MessageBoxes.WarriorMessageBox import WarriorMessageBox
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
        self.metro_placing_exist = False
        self.pull_img()

    def pull_img(self):
        self._boards = {
            str(i): self.load_and_scale((Config.app.boards_path / f"{i}.png"), [800, 800])
            for i in range(2, 6)
        }
        self._action_bg = self.load_and_scale((Config.app.boards_path / "extra_bg.png"), [268, 800])
        self._player_icon_20 = {
            _player: self.load_and_scale((Config.app.players_icons / f"{_player}.png"), [20, 20])
            for _player in ["p1", "p2", "p3", "p4", "p5"]
        }
        self._warriors_icon = {
            _player: self.load_and_scale((Config.app.boards_items / "wariors" / f"{_player}.png"), [60, 60])
            for _player in ["p1", "p2", "p3", "p4", "p5"]
        }
        self.ownership_icon = {
            _player: self.load_and_scale((Config.app.boards_items / "ownership" / f"{_player}.png"), [40, 40])
            for _player in ["p1", "p2", "p3", "p4", "p5"]
        }
        self._ships_icon = {
            _player: self.load_and_scale((Config.app.boards_items / "ships" / f"{_player}.png"), [60, 60])
            for _player in ["p1", "p2", "p3", "p4", "p5"]
        }
        self._multiplayer_icon = {
            i: self.load_and_scale((Config.app.boards_items / "multiplier" / f"{i}.png"), [20, 20])
            for i in range(1, 7)
        }
        self._play_order = self.load_and_scale((Config.app.boards_items / "order.png"), [60, 250])
        self._buildings = {
            building: [
                self.load_and_scale((Config.app.building_icons / f"{building}.png"), [40, 40]),
                self.load_and_scale((Config.app.building_icons / f"{building}_del.png"), [40, 40])
            ]
            for building in ["atena", "ares", "posejdon", "zeus"]
        }
        self._buildings["metro"] = [
            self.load_and_scale((Config.app.building_icons / "metro.png"), [40, 40]),
            self.load_and_scale((Config.app.building_icons / "metro.png"), [40, 40])
        ]
        self._income_icon = self.load_and_scale((Config.app.boards_items / "rog.png"), [30, 30])
        self.next_icon = self.org_hov((Config.app.boards_items / "next_player"), [240, 60])
        self.metro_building = {
            "not": self.load_and_scale((Config.app.background_dir / "metro_req_not.png"), [300, 300]),
            "yes": self.load_and_scale((Config.app.background_dir / "metro_req_place.png"), [300, 300]),
            "philo": self.load_and_scale((Config.app.background_dir / "metro_aten_place.png"), [300, 300])
        }
        self.yes = self.load_and_scale((Config.app.background_dir / "yes.png"), [40, 40])

    def load_hero(self):
        if (
            DataCache.get_value("new_player")
            and DataCache.get_value("act_stage") == GameState.BOARD
            and DataCache.get_value("act_hero")
        ):
            self._load_hero_layout()
            DataCache.set_value("new_player", False)

    def update_entity(self):
        _entity_to_update: dict[str, Any] = DataCache.get_value("entity_update")
        if not _entity_to_update:
            return
        logging.info("Update entities: %s", _entity_to_update.keys())
        for sprite_group in [self.entities_sprite, self.income_sprite]:
            for entity in sprite_group:
                if entity.entity_id in _entity_to_update.keys():
                    logging.info(
                        "Updated entity: %s with values %s",
                        entity.entity_id,
                        _entity_to_update[entity.entity_id]
                    )
                    entity.update_data(
                        _entity_to_update[entity.entity_id]["location"],
                        _entity_to_update[entity.entity_id]["quantity"]
                    )
        DataCache.set_value("entity_update", {})

    def draw_entities(self):
        self.income_sprite.update()
        self.building_sprite.update()
        self.entities_sprite.update()

        self.income_sprite.draw(self.screen)
        self.building_sprite.draw(self.screen)
        self.entities_sprite.draw(self.screen)

    def render_view(self):
        self.fill_bg()
        self.build_nav_bar()
        self.screen.blit(self._boards[str(DataCache.get_value("num_of_players"))], [60, 0])
        self.screen.blit(self._action_bg, [860, 0])
        self.screen.blit(self._play_order, [1140, 0])

        self.delete_entity()
        if DataCache.get_value("metro_building_build") is True:
            self.build_metro_decider_build()
        if DataCache.get_value("metro_building_philo") is True:
            self.build_metro_decider_philo()
        self.load_entity_to_buy()
        self.load_entities()
        self.load_income()
        self.add_building()
        self.update_entity()
        self.draw_entities()
        self.load_hero()
        self.build_message_box()
        self.buy_card_button()
        if DataCache.get_value("act_stage") == GameState.BOARD:
            self.next_player_button()

    def build_metro_decider_build(self):
        _selected_status = DataCache.get_value("building_to_delete")
        if all(location != -1 for location in _selected_status.values()) and len(_selected_status.keys()) == 4:
            self.build_metro_building()
            self.screen.blit(self.metro_building["yes"], (900, 250))
        else:
            self.screen.blit(self.metro_building["not"], (900, 250))
            delete_entity = DataCache.get_value("entity_delete")
            for building in self.building_sprite:
                if building._id == -1000:
                    self.building_sprite.remove(building)
                    if delete_entity:
                        delete_entity.append(-1000)
                    else:
                        delete_entity = [-1000]
                    DataCache.set_value("entity_delete", delete_entity)
                    self.metro_placing_exist = False
                    self.delete_entity()
        if "ares" in _selected_status.keys() and _selected_status["ares"] != -1:
            self.screen.blit(self.yes, (950, 285))
        if "atena" in _selected_status.keys() and _selected_status["atena"] != -1:
            self.screen.blit(self.yes, (950, 350))
        if "posejdon" in _selected_status.keys() and _selected_status["posejdon"] != -1:
            self.screen.blit(self.yes, (950, 415))
        if "zeus" in _selected_status.keys() and _selected_status["zeus"] != -1:
            self.screen.blit(self.yes, (950, 480))

    def build_metro_decider_philo(self):
        self.build_metro_building()
        self.screen.blit(self.metro_building["philo"], (900, 250))

    def build_metro_building(self):
        if not self.metro_placing_exist:
            self.metro_placing_exist = True
            self.building_sprite.add(BuildingEntity(
                -1000,
                self.screen,
                [1128, 395],
                self._buildings["metro"],
                True,
                "metro",
            ))

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
        water = Config.boards.buildings_centers[str(DataCache.get_value("num_of_players"))]
        for _, loc in water.items():
            for center in loc["small"]:
                self.draw_center(self.screen, "yellow", center, 2)
            self.draw_center(self.screen, "blue", loc["big"], 2)

    def draw_center(self, screen, color, center, radius):
        pygame.draw.circle(screen, color, tuple(center), radius)

    def delete_entity(self):
        delete_entity = DataCache.get_value("entity_delete")
        if not delete_entity:
            return
        for sprite_group in [self.entities_sprite, self.income_sprite, self.building_sprite]:
            for entity in sprite_group:
                if entity.entity_id in delete_entity:
                    self._loaded_entities.remove(entity.entity_id)
                    sprite_group.remove(entity)

        DataCache.set_value("entity_delete", [])

    @property
    def entities_icons(self) -> dict[str, dict[str, pygame.Surface]]:
        _entities_icons = {
            "warrior": self._warriors_icon,
            "ship": self._ships_icon
        }
        return _entities_icons

    @property
    def entities_class(self) -> dict[str, Callable]:
        _entities_class = {
            "warrior": WarriorEntity,
            "ship": ShipEntity
        }
        return _entities_class

    def load_entities(self):
        _fields_data: dict[str, Fieldv2] = DataCache.get_value("fields_status")
        for _field_id, _field_data in _fields_data.items():
            if not _field_data.entity._type or _field_data.entity._id in self._loaded_entities:
                continue
            self._loaded_entities.append(_field_data.entity._id)
            entity = self.entities_class[_field_data.entity._type](
                _field_data.entity._id,
                self.screen,
                _field_data.entity,
                _field_data.owner,
                _field_id,
                self.entities_icons,
                self.ownership_icon,
                self._multiplayer_icon
            )
            self.entities_sprite.add(entity)

    def load_income(self):
        fields_status: dict[str, Fieldv2] = DataCache.get_value("fields_status")
        for field_id, field_data in fields_status.items():
            if field_data.income._id in self._loaded_entities or field_data.income._id == 2:
                continue
            self._loaded_entities.append(field_data.income._id)
            income_entity = IncomeEntity(
                field_data.income._id,
                self.screen,
                field_data.income,
                field_id,
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
        _if_new = False
        fields_data: dict[str, Fieldv2] = DataCache.get_value("fields_status")
        for field_id, field_data in fields_data.items():
            if not isinstance(field_data.buildings, dict) or field_data.type != "island":
                continue
            for building_place, building_value in field_data.buildings.items():
                if isinstance(building_value, Building) and building_value._id not in self._loaded_entities:
                    building = BuildingEntity(
                        building_value._id,
                        self.screen,
                        Config.boards.buildings_centers[str(DataCache.get_value("num_of_players"))][field_id]["small"][int(building_place) - 1],
                        self._buildings[building_value.hero],
                        False,
                        building_value.hero,
                        field_id
                    )
                    self.building_sprite.add(building)
                    self._loaded_entities.append(building_value._id)
                    _if_new = True
            if field_data.metropolis[0] and field_data.metropolis[1]._id not in self._loaded_entities:
                building = BuildingEntity(
                    field_data.metropolis[1]._id,
                    self.screen,
                    field_data.metropolis[1].gui_location,
                    self._buildings[field_data.metropolis[1].hero],
                    False,
                    field_data.metropolis[1].hero,
                    field_id
                )
                self.building_sprite.add(building)
                self._loaded_entities.append(field_data.metropolis[1]._id)
                _if_new = True
        if _if_new:
            for building in self.building_sprite:
                if building._id == 2:
                    self.building_sprite.remove(building)
                if building._id == -1000:
                    self.building_sprite.remove(building)
                    self.metro_placing_exist = False
            self._load_hero_layout()

        elif DataCache.get_value("reset_building"):
            DataCache.set_value("reset_building", False)
            for building in self.building_sprite:
                if building._id == 2:
                    self.building_sprite.remove(building)
            self._load_hero_layout()

    def _load_hero_layout(self):
        if DataCache.get_value("act_hero"):
            self.heros_layout[DataCache.get_value("act_hero")]()

    def load_ares(self):
        base_building = BuildingEntity(
            2,
            self.screen,
            Config.boards.new_building_icon_loc,
            self._buildings["ares"],
            True,
            "ares"
        )
        self.building_sprite.add(base_building)

    @property
    def entity_type(self) -> Callable:
        _entity_type = {
            "ares": WarriorEntity,
            "posejdon": ShipEntity
        }
        return _entity_type[DataCache.get_value("act_hero")]

    @property
    def entity_icon(self) -> dict[str, pygame.Surface]:
        _entity_icon = {
            "ares": self._warriors_icon,
            "posejdon": self._ships_icon
        }
        return _entity_icon[DataCache.get_value("act_hero")]

    @property
    def max_entity_price(self) -> int:
        if DataCache.get_value("act_hero") in ["ares", "posejdon"]:
            return 5 if DataCache.get_value("act_hero") == "ares" else 4
        else:
            return -1

    @property
    def entity_hero(self) -> str:
        _entity_hero = {
            "ares": "warrior",
            "posejdon": "ship"
        }
        return _entity_hero[DataCache.get_value("act_hero")]

    def load_entity_to_buy(self):
        new_entity_price = DataCache.get_value("new_entity_price")
        if new_entity_price < self.max_entity_price:
            for entity in self.entities_sprite:
                if int(entity._id) * -1 == new_entity_price:
                    return
                if int(entity._id) == 0 or int(entity._id) * -1 + 1 == new_entity_price:
                    self.entities_sprite.remove(entity)
            entity_to_but = self.entities_class[self.entity_hero](
                new_entity_price * -1,
                self.screen,
                Entity(
                    new_entity_price * -1,
                    self.entity_hero,
                    1,
                ),
                DataCache.get_value("act_player"),
                "",
                self.entities_icons,
                self.ownership_icon,
                self._multiplayer_icon
            )
            self.entities_sprite.add(entity_to_but)
        elif new_entity_price == self.max_entity_price:
            for entity in self.entities_sprite:
                if int(entity._id) * -1 + 1 == new_entity_price:
                    self.entities_sprite.remove(entity)

    def load_poseidon(self):
        base_building = BuildingEntity(
            2,
            self.screen,
            Config.boards.new_building_icon_loc,
            self._buildings["posejdon"],
            True,
            "posejdon"
        )
        self.building_sprite.add(base_building)

    def load_athena(self):
        base_building = BuildingEntity(
            2,
            self.screen,
            Config.boards.new_building_icon_loc,
            self._buildings["atena"],
            True,
            "atena"
        )
        self.building_sprite.add(base_building)

    def load_zeus(self):
        base_building = BuildingEntity(
            2,
            self.screen,
            Config.boards.new_building_icon_loc,
            self._buildings["zeus"],
            True,
            "zeus"
        )
        self.building_sprite.add(base_building)

    def load_appollon(self):
        base_income = IncomeEntity(
            2,
            self.screen,
            Income(1, 2),
            "",
            self._income_icon,
            self._multiplayer_icon,
            True
        )
        self._loaded_entities.append(2)
        self.income_sprite.add(base_income)

    def load_small_apollon(self):
        pass

    def next_player_button(self):
        next_player_button = Button(
            self.screen,
            self.next_icon,
            pygame.Rect(900, 0, 240, 60),
            self.clear_player
        )
        next_player_button.update()

    def clear_player(self):
        if not DataCache.get_value("metro_building_philo") and not DataCache.get_value("metro_building_build"):
            DataCache.set_value("act_player", "")
            DataCache.set_value("act_hero", "")
            for sprite_group in [self.building_sprite, self.entities_sprite, self.income_sprite]:
                for sprite in sprite_group:
                    if sprite._id in [2, 0, -1, -2, -3, -4]:
                        sprite_group.remove(sprite)
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
            "ap_s": self.load_small_apollon
        }
        return heros

    def buy_card_button(self):
        if DataCache.get_value("athena_card"):
            athena_card = Button(
                self.screen,
                {
                    "org": self.philosophers_card,
                    "hov": self.philosophers_card
                },
                pygame.Rect(1080, 100, 60, 100),
                self.add_card_to_player
            )
            athena_card.update()

        if DataCache.get_value("zeus_card"):
            zeus_card = Button(
                self.screen,
                {
                    "org": self.priest_card,
                    "hov": self.priest_card
                },
                pygame.Rect(1080, 100, 60, 100),
                self.add_card_to_player
            )
            zeus_card.update()

    @property
    def card_hero(self) -> list:
        hero_card = {
            "atena": ["philosophers", "athena_card"],
            "zeus": ["priests", "zeus_card"]
        }
        return hero_card[DataCache.get_value("act_hero")]

    def add_card_to_player(self):
        card_status = DataCache.get_value(self.card_hero[0])
        coins_status = DataCache.get_value("coins")
        if coins_status[DataCache.get_value("act_player")] >= 4:
            DataCache.set_value(self.card_hero[1], False)

            card_status[DataCache.get_value("act_player")] += 1
            if DataCache.get_value("act_hero") == "atena":
                pygame.event.post(pygame.event.Event(EventConfig.CHECK_ATHENS))
            coins_status[DataCache.get_value("act_player")] -= 4

            DataCache.set_value(self.card_hero[0], card_status)
            DataCache.set_value("coins", coins_status)
