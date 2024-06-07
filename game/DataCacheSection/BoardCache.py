class BoardCacheSection:

    _data_cache: dict = {
        "water_status": {},
        "islands_status": {},
        "entities_status": {},
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
        "new_income_location": {},
        "income_status": {},
        "new_entity_price": 0,
        "zeus_card": False,
        "athena_card": False,
    }

    _cache_data_functions: dict = {
        "water_status": lambda x: x,
        "islands_status": lambda x: x,
        "entities_status": lambda x: x,
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
        "new_income_location": lambda x: x,
        "income_status": lambda x: x,
        "new_entity_price": lambda x: x,
        "zeus_card": lambda x: x,
        "athena_card": lambda x: x,
    }

    _base_values: dict = {}
