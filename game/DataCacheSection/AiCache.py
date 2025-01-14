class AiCacheSection:

    _data_cache: dict = {
        "ai_move_success": 0,
        "move_train_data": [],
        "valid_ai_move": True
    }

    _cache_data_functions: dict = {
        "ai_move_success": lambda x: x,
        "move_train_data": lambda x: x,
        "valid_ai_move": lambda x: x
    }

    _base_values: dict = {}
