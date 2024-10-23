from pygame import Surface
from pygame.event import Event

from ...DataCache import DataCache

from ...dataclasses.EntitiesDataClass import Entity
from ...dataclasses.FieldDataClass import Fieldv2
from ...dataclasses.IncomeDataClass import Income
from ...dataclasses.BuildingDataClass import Building
from ...enums.GameState import GameState
from ...gui.common.Config import Config
from .AbstractSubManager import AbstractSubManager


class PrepareStageManager(AbstractSubManager):

    def __init__(self, screen: Surface, stage: GameState):
        super().__init__(screen, stage)

    def handle_events(self, event: Event):
        pass

    def define_player_hero(self):
        self.read_cache_values()
        player_order = DataCache.get_value("play_order")
        player_hero = DataCache.get_value("hero_players")
        if player_order and not self._act_player:
            self._act_player = player_order[0]
            DataCache.set_value("play_order", player_order[1:])
            self._act_hero = player_hero[self._act_player]
            DataCache.set_value("new_entity_price", 0)
            DataCache.set_value("athena_card", False)
            DataCache.set_value("zeus_card", False)
            if self._act_hero == "ares":
                DataCache.set_value("new_entity_price", 0)
            elif self._act_hero == "posejdon":
                DataCache.set_value("new_entity_price", 0)
            elif self._act_hero == "atena":
                self._add_atena_card(self._act_player)
                DataCache.set_value("athena_card", True)
            elif self._act_hero == "zeus":
                self._add_zeus_card(self._act_player)
                DataCache.set_value("zeus_card", True)
            else:
                self._calc_apollon_money(self._act_player)
        self.save_cache_values()

    @staticmethod
    def _calc_apollon_money(act_player):
        _fields_status = DataCache.get_value("fields_status")
        num_of_is = 0
        coins_for_player = DataCache.get_value("coins")
        for _, field_data in _fields_status.items():
            if field_data.type == "island" and field_data.owner == act_player:
                num_of_is += 1
        if num_of_is > 1:
            coins_for_player[act_player] += 1
        else:
            coins_for_player[act_player] += 4
        DataCache.set_value("coins", coins_for_player)

    @staticmethod
    def _add_zeus_card(act_player):
        priest_per_player = DataCache.get_value("priests")
        priest_per_player[act_player] += 1
        DataCache.set_value("priests", priest_per_player)

    @staticmethod
    def _add_atena_card(act_player):
        philosophers_per_player = DataCache.get_value("philosophers")
        philosophers_per_player[act_player] += 1
        DataCache.set_value("philosophers", philosophers_per_player)

    def setup_board_first_stage(self):
        _water_config = Config.boards.water_config[str(DataCache.get_value("num_of_players"))]
        _field_status = {}
        for circle, base_config in _water_config.items():
            if base_config["owner"]:
                _player, quantity = next(iter(base_config["owner"].items()))
                _field_status[circle] = Fieldv2(
                    "water",
                    _player,
                    base_config["base_income"],
                    Entity(
                        self.generate_unique_id(),
                        "ship",
                        quantity
                    )
                )
            else:
                _field_status[circle] = Fieldv2(
                    "water",
                    "None",
                    base_config["base_income"]
                )

        _islands_config = Config.boards.islands_config[str(DataCache.get_value("num_of_players"))]
        for island, base_config in _islands_config.items():
            if base_config["owner"]:
                _player, quantity = next(iter(base_config["owner"].items()))
                _field_status[island] = Fieldv2(
                    "island",
                    _player,
                    base_config["base_income"],
                    Entity(
                        self.generate_unique_id(),
                        "warrior",
                        quantity
                    ),
                    {key: None for key in base_config["buildings"]["small"]},
                    (False, Building(2, "", [])),
                    Income(0)
                )
            else:
                _field_status[island] = Fieldv2(
                    "island",
                    "None",
                    base_config["base_income"],
                    Entity(None, None, 0),
                    {key: None for key in base_config["buildings"]["small"]},
                    (False, Building(2, "", [])),
                    Income(0)
                )
        DataCache.set_value("fields_status", _field_status)

    def read_cache_values(self):
        return super().read_cache_values()

    def save_cache_values(self):
        return super().save_cache_values()

    def end_stage(self):
        _coins = DataCache.get_value("coins")
        income_pre_round = self.calculate_income()
        for player, income in income_pre_round.items():
            _coins[player] += income
        DataCache.set_value("coins", _coins)
        DataCache.set_value("act_stage", GameState.ROLL)
        bid_order = []
        for row, bid in DataCache.get_value("bids_value").items():
            if row != "row_5" and bid:
                bid_order.append(bid["player"])
            elif row == "row_5":
                for player_appollon_bid in bid:
                    bid_order.append(player_appollon_bid)
        DataCache.set_value("bid_order", bid_order)
        if self.check_win:
            print(self.check_win)
        DataCache.reset_stage(GameState.ROLL)

    @staticmethod
    def calculate_income():
        _fields_status = DataCache.get_value("fields_status")
        players_name = {f"p{num}": 0 for num in range(1, 6)}
        for _, field_data in _fields_status.items():
            if field_data.owner in players_name.keys():
                players_name[field_data.owner] += field_data.base_income
                if field_data.income:
                    players_name[field_data.owner] += field_data.income.quantity
        return players_name

    @property
    def check_win(self) -> list[str]:
        players_status = {}
        for _, field_data in DataCache.get_value("fields_status").items():
            if field_data.type == "island" and field_data.metropolis:
                if field_data.owner in players_status.keys():
                    players_status[field_data.owner] += 1
                else:
                    players_status[field_data.owner] = 1
        wining_players = []
        for player, num_of_metro in players_status.items():
            if num_of_metro == 2:
                wining_players.append(player)
        return wining_players
