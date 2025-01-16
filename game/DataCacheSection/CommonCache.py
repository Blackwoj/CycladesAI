class CommonCache:

    _data_cache: dict = {
        "act_player": "",
        "act_stage": "",
        "act_hero": "",
        "num_of_players": 5,
        "play_order": [],
        "is_dragging": False,
        "new_player": True,
        "board_view": ""
    }

    _cache_data_functions: dict = {
        "act_player": lambda x: x,
        "act_stage": lambda x: x,
        "act_hero": lambda x: x,
        "num_of_players": lambda x: x,
        "play_order": lambda x: x,
        "is_dragging": lambda x: x,
        "new_player": lambda x: x,
        "board_view": lambda x: x
    }

    _base_values: dict = {}
