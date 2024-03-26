from typing import Literal, Union

from .enums.GameState import GameState
from .DataCacheSection.RollCache import RollCacheSection
from .DataCacheSection.CommonCache import CommonCache
from .DataCacheSection.PlayerCache import PlayerCache


class DataCache:

    _cache_sections: list = [
        RollCacheSection,
        CommonCache,
        PlayerCache
    ]

    AvailableSections = Literal[
        "game_config",
        "num_of_players",
        "act_player",
        "act_stage",
        "coins",
        "priests",
        "philosophers",
        "hero_players",
        "bids_value",
        "temp_bid",
        "bid_order",
        "bids_order",
        "heros_per_row",
        "left_heros",
    ]

    _data_cache: dict = {}
    _cache_data_functions: dict = {}

    @classmethod
    def initialize_cache(cls):
        cls._data_cache = {
            key: value for cache_cls in cls._cache_sections for (key, value) in cache_cls._data_cache.items()
        }

        cls._cache_data_functions = {
            key: value for cache_cls in cls._cache_sections for (key, value) in cache_cls._cache_data_functions.items()
        }

    @staticmethod
    def set_value(key: AvailableSections, value: Union[dict, str, list, int, GameState]):
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
