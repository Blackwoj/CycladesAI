from pygame import Surface
from pygame.event import Event
from .AbstractSubManager import AbstractSubManager
from ...enums.GameState import GameState
from ...DataCache import DataCache
from ...gui.common.Config import Config
from ...dataclasses.FieldDataClass import Field
from ...dataclasses.EntitiesDataClass import Entity


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
                print(self._act_player)
                self._calc_apollon_money(self._act_player)
        self.save_cache_values()

    @staticmethod
    def _calc_apollon_money(act_player):
        _act_islands_status = DataCache.get_value("islands_status")
        num_of_is = 0
        coins_for_player = DataCache.get_value("coins")
        for _, island_data in _act_islands_status.items():
            if island_data.owner == act_player:
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
        _water_status = {}
        _islands_status = {}
        _entities_status = {}
        for circle, base_config in _water_config.items():
            if base_config["owner"]:
                _player, quantity = next(iter(base_config["owner"].items()))
                _entities_status[self.generate_unique_id()] = Entity("ship", _player, quantity, circle)
                _water_status[circle] = Field("water", _player, quantity, base_config["base_income"])
            else:
                _water_status[circle] = Field("Water", "None", 0, base_config["base_income"])

        _islands_config = Config.boards.islands_config
        for island, base_config in _islands_config[str(DataCache.get_value("num_of_players"))].items():
            if base_config["owner"]:
                _player, quantity = next(iter(base_config["owner"].items()))
                _islands_status[island] = Field(
                    "island",
                    _player,
                    quantity,
                    base_config["base_income"],
                    {key: "" for key in base_config["buildings"]["small"]},
                    False,
                    0
                )
                _entities_status[self.generate_unique_id()] = Entity("warrior", _player, quantity, island)
            else:
                _islands_status[island] = Field(
                    "island",
                    "None",
                    0,
                    base_config["base_income"],
                    {key: "" for key in base_config["buildings"]["small"]},
                    False,
                    0
                )
        DataCache.set_value("entities_status", _entities_status)
        DataCache.set_value("islands_status", _islands_status)
        DataCache.set_value("water_status", _water_status)

    def read_cache_values(self):
        return super().read_cache_values()

    def save_cache_values(self):
        return super().save_cache_values()

    def end_stage(self):
        _coins = DataCache.get_value("coins")
        income_pre_round = self.calculate_income(
            DataCache.get_value("islands_status"),
            DataCache.get_value("water_status")
        )
        for player, income in income_pre_round.items():
            _coins[player] += income
        DataCache.set_value("coins", _coins)
        DataCache.set_value("act_stage", GameState.ROLL)
        DataCache.reset_stage(GameState.ROLL)

    @staticmethod
    def calculate_income(_island_status: dict[int, Field], _water_status: dict[int, Field]):
        players_name = {f"p{num}": 0 for num in range(1, 6)}
        for filed_status in [_island_status, _water_status]:
            for _, field_data in filed_status.items():
                if field_data.owner in players_name.keys():
                    players_name[field_data.owner] += field_data.base_income
                    players_name[field_data.owner] += field_data.income
        return players_name

    @property
    def check_win(self):
        players_status = {}
        for island_id, island_data in DataCache.get_value("islands_status"):
            if island_data.metropolis:
                if island_data.owner in players_status.keys():
                    players_status[island_data.owner] += 1
                else:
                    players_status[island_data.owner] = 1
        wining_players = []
        for player, num_of_metro in players_status.items():
            if num_of_metro == 2:
                wining_players.append(player)
        return wining_players
