from ..dataclasses.FieldDataClass import Fieldv2
from ..dataclasses.PlayerDataClass import PlayerDataclass
from typing import Any
from ..gui.common.Config import Config
from ..graph import Graph


class RewardCalculator:
    def __init__(self):
        self.fields_data: dict[str, Fieldv2]
        self.islands_config: dict[str, dict[str, Any]] = Config.boards.islands_config["5"]
        self.players_data: dict[str, PlayerDataclass]
        self.player_reward: list[int] = []
        self.graph = Graph()
        # self.fill_graph()

        # Wagi poszczególnych komponentów
        self.weights = {
            "coins": 1,
            "priests": 6,
            "philosophers": 10,
            "income": 5,
            "building": 3,
            "entities": 3,
            "metropolises": 100
        }

    def calculate_reward(
        self,
        fields_data: dict[str, Fieldv2],
        players_data: dict[str, PlayerDataclass]
    ) -> list[int]:
        self.player_reward = [0, 0, 0, 0, 0]
        self.fields_data = fields_data
        self.players_data = players_data

        self._calculate_player_assets()
        self._calculate_islands_assets()
        self._calculate_entities_assets()
        self._calculate_metro_assets()
        return self.player_reward

    def _calculate_player_assets(self):
        for _, player in self.players_data.items():
            player_index = int(player._player_id[1]) - 1
            self.player_reward[player_index] += (
                player.coins * self.weights["coins"]
                + player.philosophers * self.weights["philosophers"]
                + player.priests * self.weights["priests"]
            )

    def _calculate_islands_assets(self):
        players_building = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        for _, field in self.fields_data.items():
            if field.type == "island" and field.owner != "None":
                player_index = int(field.owner[1]) - 1
                total_income = field.base_income + field.income.quantity

                all_bundlings = field.get_all_building
                for building_index in range(len(players_building[player_index])):
                    players_building[player_index][building_index] += all_bundlings[building_index]
                diff_buildings_num = len([x for x in players_building[player_index] if x != 0])
                diff_buildings_num = 1 if not diff_buildings_num else diff_buildings_num
                # Dodajemy wartość za budynki
                building_value = sum(
                    5 if b and b.hero and b.hero != "None" else 0 for b in (field.buildings or {}).values()
                )
                self.player_reward[player_index] += (
                    self.weights["income"] * total_income
                    + self.weights["building"] * building_value * diff_buildings_num
                )

    def _calculate_entities_assets(self):
        for _, field in self.fields_data.items():
            if field.owner != "None":
                player_index = int(field.owner[1]) - 1
                self.player_reward[player_index] += (
                    self.weights["entities"] * field.entity.quantity
                )

    def _calculate_metro_assets(self):
        for _, field in self.fields_data.items():
            if field.metropolis[0]:  # Jeśli metropolia istnieje
                player_index = int(field.owner[1]) - 1
                self.player_reward[player_index] += self.weights["metropolises"]

    # def _calculate_island_safety(self):
    #     pass

    # def fill_graph(self):
    #     _water_config = Config.boards.water_config
    #     for ver in _water_config["5"].keys():
    #         self.graph.add_vertex(ver, "None")
    #     _island_vertex = Config.boards.islands_config
    #     for ver in _island_vertex["5"].keys():
    #         self.graph.add_vertex(ver, "None")
    #     for ver, ver_config in _water_config["5"].items():
    #         for neighbors in ver_config["neighbors"]:
    #             self.graph.add_edge(ver, neighbors)
    #         for neighbors in ver_config["neighbors_island"]:
    #             self.graph.add_edge(ver, neighbors)
