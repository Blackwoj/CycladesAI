from pygame import Surface
from pygame.event import Event
from .AbstractSubManager import AbstractSubManager
from ...enums.GameState import GameState
from ...DataCache import DataCache
from ...gui.common.Config import Config


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
        self.save_cache_values()

    def setup_board_first_stage(self):
        _water_config = Config.boards.water_config
        _ships_status = {}
        _water_status = {}
        _islands_status = {}
        _warriors_status = {}
        for circle, base_config in _water_config[str(DataCache.get_value("num_of_players"))].items():
            if base_config["owner"]:
                _player, _num_of_entities = next(iter(base_config["owner"].items()))
                _ships_status[self.generate_unique_id()] = {
                    "owner": _player,
                    "num_of_entities": _num_of_entities,
                    "field": circle,
                }
                _water_status[circle] = {
                    "owner": _player,
                    "num_of_entities": _num_of_entities,
                    "base_income": base_config["base_income"],
                }
            else:
                _water_status[circle] = {
                    "owner": "None",
                    "num_of_entities": 0,
                    "base_income": base_config["base_income"],
                }
        _islands_config = Config.boards.islands_config
        for island, base_config in _islands_config[str(DataCache.get_value("num_of_players"))].items():
            if base_config["owner"]:
                _player, _num_of_entities = next(iter(base_config["owner"].items()))
                _islands_status[island] = {
                    "owner": _player,
                    "num_of_entities": _num_of_entities,
                    "base_income": base_config["base_income"],
                    "income": 0,
                    "building": {
                        "small": {
                            key: "" for key in base_config["buildings"]["small"]
                        },
                        "big": False
                    }
                }
                _warriors_status[self.generate_unique_id()] = {
                    "owner": _player,
                    "num_of_entities": _num_of_entities,
                    "field": island
                }
            else:
                _islands_status[island] = {
                    "owner": "None",
                    "num_of_entities": 0,
                    "base_income": base_config["base_income"],
                    "income": 0,
                    "building": {
                        "small": {
                            key: "" for key in base_config["buildings"]["small"]
                        },
                        "big": False
                    }
                }
        DataCache.set_value("ship_status", _ships_status)
        DataCache.set_value("islands_status", _islands_status)
        DataCache.set_value("warriors_status", _warriors_status)
        DataCache.set_value("water_status", _water_status)

    def read_cache_values(self):
        return super().read_cache_values()

    def save_cache_values(self):
        return super().save_cache_values()
