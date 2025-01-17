class BoardCacheSection:

    _data_cache: dict = {
        "fields_status": {},
        "new_warrior_location": (),
        "new_ship_location": (),
        "message_board": "",
        "entity_update": {},
        "entity_delete": [],
        "posejdon_move": 0,
        "new_building_location": [],
        "reset_building": False,
        "new_income_location": {},
        "new_entity_price": 0,
        "zeus_card": False,
        "athena_card": False,
        "metro_building_build": False,
        "metro_building_philo": False,
        "building_to_delete": {}
    }

    _cache_data_functions: dict = {
        "fields_status": lambda x: x,
        "new_warrior_location": lambda x: x,
        "message_board": lambda x: x,
        "entity_update": lambda x: x,
        "entity_delete": lambda x: x,
        "posejdon_move": lambda x: x,
        "new_building_location": lambda x: x,
        "reset_building": lambda x: x,
        "new_ship_location": lambda x: x,
        "new_income_location": lambda x: x,
        "new_entity_price": lambda x: x,
        "zeus_card": lambda x: x,
        "athena_card": lambda x: x,
        "metro_building_build": lambda x: x,
        "metro_building_philo": lambda x: x,
        "building_to_delete": lambda x: x,
    }

    _base_values: dict = {}
