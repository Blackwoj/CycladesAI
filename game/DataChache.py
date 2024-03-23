from typing import Literal, Union

from .enums.GameState import GameState


class DataCache:

    AvailableSections = Literal[
        "game_config",
        "players_items",
        "num_of_players",
        "bids_value",
        "temp_bid",
        "bid_order",
        "act_player",
        "act_stage",
        "players_items",
        "coins",
        "priests",
        "philosophers",
        "bids_order",
        "hero_players",
        "heros_per_row",
        "left_heros",
    ]

    _data_cache: dict = {
        "act_player": "",
        "act_stage": "",
        "hero_players": {
            "p1": "None",
            "p2": "None",
            "p3": "None",
            "p4": "None",
            "p5": "None",
        },
        "game_config": [],

        "coins": {
            "p1": 10,
            "p2": 10,
            "p3": 10,
            "p4": 10,
            "p5": 10
        },
        "priests": {
            "p1": 10,
            "p2": 10,
            "p3": 5,
            "p4": 5,
            "p5": 10
        },
        "philosophers": {
            "p1": 1,
            "p2": 0,
            "p3": 0,
            "p4": 0,
            "p5": 0
        },

        "num_of_players": 5,

        "bid_order": [],
        "bids_value": {
            "row_1": {
            },
            "row_2": {
            },
            "row_3": {
            },
            "row_4": {
            },
            "row_5": []
        },
        "heros_per_row": {
            "row_1": "",
            "row_2": "",
            "row_3": "",
            "row_4": ""
        },
        "temp_bid": 0,
        "bids_order": [],
        "left_heros": []
    }
    _cache_data_functions: dict = {
        "act_player": lambda x: x,
        "act_stage": lambda x: x,
        "game_config": lambda x: x,
        "num_of_players": lambda x: x,

        "bid_order": lambda x: x,
        "bids_value": lambda x: x,
        "temp_bid": lambda x: x,

        "coins": lambda x: x,
        "priests": lambda x: x,
        "philosophers": lambda x: x,
        "hero_players": lambda x: x,
        "heros_per_row": lambda x: x,
        "left_heros": lambda x: x
    }

    @staticmethod
    def set_value(
        key: AvailableSections,
        value: Union[dict, str, list, int, GameState]
    ):
        if key in DataCache._data_cache:
            DataCache._data_cache[key] = DataCache._cache_data_functions[key](value)
        else:
            raise AttributeError(f"'{type(DataCache).__name__}' object has no attribute '{key}'")

    @staticmethod
    def get_value(
        key: AvailableSections,
    ):
        if key in DataCache._data_cache:
            return DataCache._data_cache.get(key, None)
        else:
            raise AttributeError(f"'{type(DataCache).__name__}' object has no attribute '{key}'")
