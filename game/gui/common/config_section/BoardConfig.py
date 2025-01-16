import json
from pathlib import Path


class BoardConfig:
    circles_centers: dict = {
        str(5): json.loads((
            Path(__file__).resolve().parent / "boards" / "water_centers" / f"{5}.json"
        ).open().read())
    }

    buildings_centers: dict = {
        str(5): json.loads((
            Path(__file__).resolve().parent / "boards" / "buildings_centers" / f"{5}.json"
        ).open().read())
    }

    warriors_points: dict = {
        str(5): json.loads((
            Path(__file__).resolve().parent / "boards" / "warriors_points" / f"{5}.json"
        ).open().read())
    }

    income_point: dict = {
        str(5): json.loads((
            Path(__file__).resolve().parent / "boards" / "income_points" / f"{5}.json"
        ).open().read())
    }

    water_config: dict = {
        str(5): json.loads((
            Path(__file__).resolve().parent / "boards" / "base_fileds_value" / f"water_{5}.json"
        ).open().read())
    }

    islands_config: dict = {
        str(5): json.loads((
            Path(__file__).resolve().parent / "boards" / "base_fileds_value" / f"island_{5}.json"
        ).open().read())
    }

    new_building_icon_loc = [1036, 300]
    building_price_loc = [new_building_icon_loc[0] - 40, new_building_icon_loc[1]]

    new_special_event_loc = [1036, 210]
    special_event_price_loc = [new_special_event_loc[0] - 40, new_special_event_loc[1]]

    ares_pricing = [0, 2, 3, 4]
    posejdon_pricing = [0, 1, 2, 3]

    default_max_len = 2**64

    calc_buildings_help_dict = {
        player: {
            building: 0 for building in ["ares", "atena", "zeus", "ares", "posejdon"]
        } for player in ["p" + str(i) for i in range(1, 6)]
    }
