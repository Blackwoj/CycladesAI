class BoardCacheSection:

    _data_cache: dict = {
        "water_status": {},
        "islands_status": {},
        "warriors_status": {},
        "buildings_status": {},
        "new_warrior_location": (),
        "new_ship_location": (),
        "message_board": "",
        "entity_update": {},
        "entity_delete": [],
        "posejdon_move": 0,
        "board_row": [],
        "player_god": {},
        "new_building": [],
        "reset_building": False,
        "ship_status": {},
        "new_income_location": {},
        "income_status": {}
    }

    _cache_data_functions: dict = {
        "water_status": lambda x: x,
        "islands_status": lambda x: x,
        "warriors_status": lambda x: x,
        "new_warrior_location": lambda x: x,
        "message_board": lambda x: x,
        "entity_update": lambda x: x,
        "entity_delete": lambda x: x,
        "posejdon_move": lambda x: x,
        "board_row": lambda x: x,
        "player_god": lambda x: x,
        "new_building": lambda x: x,
        "buildings_status": lambda x: x,
        "reset_building": lambda x: x,
        "new_ship_location": lambda x: x,
        "ship_status": lambda x: x,
        "new_income_location": lambda x: x,
        "income_status": lambda x: x
    }
