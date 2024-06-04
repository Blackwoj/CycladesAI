class PlayerCache:

    _data_cache: dict = {
        "hero_players": {
            "p1": "None",
            "p2": "None",
            "p3": "None",
            "p4": "None",
            "p5": "None",
        },
        "coins": {
            "p1": 5,
            "p2": 5,
            "p3": 5,
            "p4": 5,
            "p5": 5
        },
        "priests": {
            "p1": 0,
            "p2": 0,
            "p3": 0,
            "p4": 0,
            "p5": 0
        },
        "philosophers": {
            "p1": 0,
            "p2": 0,
            "p3": 0,
            "p4": 0,
            "p5": 0
        }
    }

    _cache_data_functions: dict = {
        "coins": lambda x: x,
        "priests": lambda x: x,
        "philosophers": lambda x: x,
        "hero_players": lambda x: x,
    }

    _base_values: dict = {}
