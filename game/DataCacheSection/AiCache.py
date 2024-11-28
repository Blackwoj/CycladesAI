class AiCacheSection:

    _data_cache: dict = {
        "success": 0,
        "move_data": [],
        "valid_ai_move": True
    }

    _cache_data_functions: dict = {
        "success": lambda x: x,
        "move_data": lambda x: x,
        "valid_ai_move": lambda x: x
    }

    _base_values: dict = {}
