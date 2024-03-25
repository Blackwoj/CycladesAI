class CommonCache:

    _data_cache: dict = {
        "hero_players": {
            "p1": "None",
            "p2": "None",
            "p3": "None",
            "p4": "None",
            "p5": "None",
        },
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
        }
    }

    _cache_data_functions: dict = {
        "coins": lambda x: x,
        "priests": lambda x: x,
        "philosophers": lambda x: x,
        "hero_players": lambda x: x,
    }
