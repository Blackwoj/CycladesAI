from ..DataCache import DataCache
from ..Models.Model import CycladesAI
from ..dataclasses.FieldDataClass import Fieldv2
from ..dataclasses.BuildingDataClass import Building
from ..dataclasses.EntitiesDataClass import Entity
from ..dataclasses.PlayerDataClass import PlayerDataclass
from .RewardCalculator import RewardCalculator
from ..enums.GameState import GameState
from typing import Union
from copy import deepcopy

class ConnectModel:

    def __init__(self):
        self.model = CycladesAI()
        self.model.load_model()
        self._reward_calculator = RewardCalculator()
        self._pre_state: list[int] = []
        self._pre_reward_player: list[int] = [0, 0, 0, 0, 0]

    def train_on_state(self):
        # _move_data = DataCache.get_value("move_data")
        # _act_state = self._get_state
        # _act_reward = self._calculate_player_reward(_act_state)
        # _reward_diff = [
        #     _act_reward[i] - self._pre_reward[i]
        #     for i in range(len(self._pre_reward))
        # ]
        DataCache.set_value("move_data", [])

    def predict_state(self):
        state = self._get_state

        if DataCache.get_value("act_stage") == GameState.ROLL:
            hero_row: dict[str, str] = DataCache.get_value("heros_per_row")
            bids: dict[str, dict[str, Union[str, int]]] = DataCache.get_value("bids_value")
            hero_bid = {
                "row_5": [
                    "apollon",
                    len(bids["row_5"]) - 1
                ]
            }
            for row in hero_row.keys():
                if "5" in row:
                    continue
                hero_bid[row] = [
                    hero_row[row],
                    0 if not bids[row] else bids[row]["bid"]
                ]
            self.model.RollModel.predict(state, hero_bid)
        elif DataCache.get_value("act_stage") == GameState.BOARD:
            pass
        pass

    def predict_ares(self):
        pass

    def predict_atena(self):
        pass

    def predict_zeus(self):
        pass

    def predict_posejdon(self):
        pass

    def predict_roll(self):
        pass

    def save_pre_state(self):
        self._pre_state = self._get_state
        self._pre_reward = self._calculate_player_reward(self._get_state)

    @property
    def _get_state(self) -> list:
        fields_data: dict[str, Fieldv2] = DataCache.get_value("fields_status")
        players_data: dict[str, PlayerDataclass] = DataCache.get_value("player_data")
        state = []
        for _, field_data in fields_data.items():
            state.extend(field_data.to_binary())
        for _, player_data in players_data.items():
            state.extend(player_data.to_binary())
        if DataCache.get_value("act_hero") == "ares":
            state.append(DataCache.get_value("new_entity_price"))
            state.append(-1)
        if DataCache.get_value("act_hero") == "posejdon": 
            state.append(-1)
            state.append(DataCache.get_value("new_entity_price"))
        state.extend(
            [
                int(DataCache.get_value("zeus_card")),
                int(DataCache.get_value("athena_card"))
            ]
        )
        state.append(self._player_to_id)
        return state

    def _calculate_player_reward(self, state: list[int] = []) -> list[int]:
        fields_data: dict[str, Fieldv2] = DataCache.get_value("fields_status")
        players_data: dict[str, PlayerDataclass] = DataCache.get_value("player_data")
        _temp_fields_data: dict[str, Fieldv2] = {}
        _temp_player_data: dict[str, PlayerDataclass] = {}
        if not state:
            _temp_fields_data = fields_data
            _temp_player_data = players_data
        else:
            _temp_fields_data = self.read_fields_from_state(state)
            _temp_player_data = self.read_players_form_state(state)

        return self._reward_calculator.calculate_reward(_temp_fields_data, _temp_player_data)

    def read_fields_from_state(self, state) -> dict[str, Fieldv2]:
        _fields_data: dict[str, Fieldv2] = DataCache.get_value("fields_status")
        _temp_fields_data: dict[str, Fieldv2] = {}
        index_start = 0
        for field_id, field_data in _fields_data.items():
            if field_data.type == "water":
                filed_config = state[index_start:index_start + 3]
                _temp_fields_data[field_id] = Fieldv2(
                    "water",
                    "None" if filed_config[0] == 0 else "p" + str(filed_config[0]),
                    filed_config[1],
                    Entity(None, None, filed_config[2])
                )
                index_start += 3
            if field_data.type == "island":
                filed_config = state[index_start:index_start + 8]
                _temp_fields_data[field_id] = Fieldv2(
                    "island",
                    "None" if filed_config[0] == 0 else "p" + str(filed_config[0]),
                    filed_config[1],
                    Entity(None, None, filed_config[2]),
                    {
                        str(place + 1): Building(-1, self._int_hero_to_building(str(hero)), [0, 0])
                        for place, hero in enumerate(filed_config[3:7])
                        if hero != -1
                    },
                    (
                        True if filed_config[7] else False,
                        Building(2, "", [])
                    )
                )
                index_start += 8
        _state = []
        for _, field_data in _fields_data.items():
            _state.extend(field_data.to_binary())
        return _temp_fields_data

    def read_players_form_state(self, state) -> dict[str, PlayerDataclass]:
        _temp_player_data: dict[str, PlayerDataclass] = {}
        players_data = [state[-15:][i:i + 3] for i in range(0, len(state[-15:]), 3)]
        for player_num, player_data in enumerate(players_data):
            _temp_player_data["p" + str(player_num + 1)] = PlayerDataclass(
                "p" + str(player_num + 1),
                player_data[0],
                player_data[1],
                player_data[2],
            )

        _state = []
        _players_data: dict[str, PlayerDataclass] = DataCache.get_value("player_data")
        for _, player_data in _players_data.items():
            _state.extend(player_data.to_binary())
        return _temp_player_data

    @staticmethod
    def _int_hero_to_building(int_value: str) -> str:
        hero_id = {
            "0": "None",
            "1": "ares",
            "2": "atena",
            "3": "posejdon",
            "4": "zeus"
        }
        return hero_id[int_value]

    @property
    def _player_to_id(self):
        player_id = {
            "p1": 1,
            "p2": 2,
            "p3": 3,
            "p4": 4,
            "p5": 5
        }
        return player_id[DataCache.get_value("act_player")]
