class CommonCache:

    _data_cache: dict = {
        "act_player": "",
        "act_stage": "",
        "game_config": [],
        "num_of_players": 5,
        "play_order": []
    }

    _cache_data_functions: dict = {
        "act_player": lambda x: x,
        "act_stage": lambda x: x,
        "game_config": lambda x: x,
        "num_of_players": lambda x: x,
        "play_order": lambda x: x
    }
