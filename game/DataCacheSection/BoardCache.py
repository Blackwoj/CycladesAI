class BoardCacheSection:

    _data_cache: dict = {
        "water_status": {},
        "islands_status": {},
        "warriors_status": {},
        "new_warrior_location": (),
    }

    _cache_data_functions: dict = {
        "water_status": lambda x: x,
        "islands_status": lambda x: x,
        "warriors_status": lambda x: x,
        "new_warrior_location": lambda x: x,
    }
