from ..dataclasses.PlayerDataClass import PlayerDataclass


class PlayerCache:

    _data_cache: dict = {
        "hero_players": {
            "p1": "None",
            "p2": "None",
            "p3": "None",
            "p4": "None",
            "p5": "None",
        },
        "player_data": {
            "p1": PlayerDataclass(
                "p1",
                5,
            ),
            "p2": PlayerDataclass(
                "p2",
                5,
            ),
            "p3": PlayerDataclass(
                "p3",
                5,
            ),
            "p4": PlayerDataclass(
                "p4",
                5,
            ),
            "p5": PlayerDataclass(
                "p5",
                5,
                2
            )
        }
    }

    _cache_data_functions: dict = {
        "player_data": lambda x: x,
        "hero_players": lambda x: x,
    }
