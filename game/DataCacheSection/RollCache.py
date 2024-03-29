class RollCacheSection:

    _data_cache: dict = {
        "bid_order": [],
        "bids_value": {
            "row_1": {
            },
            "row_2": {
            },
            "row_3": {
            },
            "row_4": {
            },
            "row_5": []
        },
        "heros_per_row": {
            "row_1": "",
            "row_2": "",
            "row_3": "",
            "row_4": "",
            "row_5": ""
        },
        "temp_bid": 0,
        "bids_order": [],
        "left_heros": []
    }

    _cache_data_functions: dict = {
        "bid_order": lambda x: x,
        "bids_value": lambda x: x,
        "temp_bid": lambda x: x,
        "heros_per_row": lambda x: x,
        "left_heros": lambda x: x
    }
