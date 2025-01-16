from copy import deepcopy
from typing import Literal, Union

from .DataCacheSection.BoardCache import BoardCacheSection
from .DataCacheSection.CommonCache import CommonCache
from .DataCacheSection.PlayerCache import PlayerCache
from .DataCacheSection.RollCache import RollCacheSection
from .DataCacheSection.AiCache import AiCacheSection
from .enums.GameState import GameState
from pygame import Surface


class DataCache:

    _cache_sections: dict = {
        GameState.ROLL: RollCacheSection,
        "Common": CommonCache,
        "Player": PlayerCache,
        GameState.BOARD: BoardCacheSection,
        "Ai": AiCacheSection,
    }

    AvailableSections = Literal[
        # "game_config",
        "num_of_players",
        "board_view",

        "act_player",
        "act_stage",
        "act_hero",
        "new_player",
        "play_order",
        "hero_players",

        "heros_per_row",
        "bid_order",
        "bids_value",
        "temp_bid",

        "player_data",
        "fields_status",
        "new_warrior_location",
        "new_ship_location",
        "new_income_location",
        "new_building_location",
        "reset_building",
        "entity_delete",
        "entity_update",

        "posejdon_move",
        "new_entity_price",
        "zeus_card",
        "athena_card",

        "message_board",
        "is_dragging",
        "left_heros",

        "metro_building_build",
        "metro_building_philo",
        "building_to_delete",

        "ai_move_success",
        "move_train_data",
        "valid_ai_move",
    ]

    _data_cache: dict = {}
    _cache_data_functions: dict = {}

    @classmethod
    def initialize_cache(cls):
        cls._data_cache = {
            key: value for cache_cls in cls._cache_sections.values() for (key, value) in cache_cls._data_cache.items()
        }

        cls._cache_data_functions = {
            key: value for cache_cls in cls._cache_sections.values() for (key, value) in cache_cls._cache_data_functions.items()
        }

    @staticmethod
    def set_value(key: AvailableSections, value: Union[dict, str, list, int, GameState, Surface]):
        if key in DataCache._data_cache:
            DataCache._data_cache[key] = DataCache._cache_data_functions[key](value)
        else:
            raise AttributeError(f"'{type(DataCache).__name__}' object has no attribute '{key}'")

    @staticmethod
    def get_value(key: AvailableSections):
        if key in DataCache._data_cache:
            return DataCache._data_cache.get(key, None)
        else:
            raise AttributeError(f"'{type(DataCache).__name__}' object has no attribute '{key}'")

    @classmethod
    def reset_stage(cls, stage):
        for _cache_setting, _cache_value in cls._cache_sections[stage]._base_values.items():
            cls._data_cache[_cache_setting] = deepcopy(_cache_value)
