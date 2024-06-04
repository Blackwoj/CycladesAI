class CommonCache:

    _data_cache: dict = {
        "act_player": "",
        "act_stage": "",
        "act_hero": "",
        "game_config": [],
        "num_of_players": 5,
        "play_order": [],
        "is_dragging": False,
        "new_player": True
    }

    _cache_data_functions: dict = {
        "act_player": lambda x: x,
        "act_stage": lambda x: x,
        "act_hero": lambda x: x,
        "game_config": lambda x: x,
        "num_of_players": lambda x: x,
        "play_order": lambda x: x,
        "is_dragging": lambda x: x,
        "new_player": lambda x: x
    }

    _base_values: dict = {}
