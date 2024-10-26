from dataclasses import dataclass
from typing import Optional

from .BuildingDataClass import Building
from .EntitiesDataClass import Entity
from .IncomeDataClass import Income
from .AbstractDataClass import AbstractDataclass


@dataclass
class Fieldv2(AbstractDataclass):
    type: str
    owner: str
    base_income: int = 0
    entity: Entity = Entity(None, None, 0)
    buildings: Optional[dict[str, Optional[Building]]] = None
    metropolis: tuple[bool, Building] = (False, Building(2, "", []))
    income: Income = Income(0, 2)

    def to_binary(self):
        if self.type == "island":
            return self._island_to_binary()
        elif self.type == "water":
            return self._water_to_binary()
        else:
            raise NotImplementedError

    def _island_to_binary(self):
        income = self.base_income + self.income.quantity
        if self.buildings:
            buildings = [
                self._hero_building_to_int(hero)
                if hero else 0
                for hero in self.buildings.keys()
            ]
            while len(buildings) < 4:
                buildings.append(-1)
        else:
            buildings = [-1, -1, -1, -1]
        return [
            self._player_int,
            income,
            self.entity.quantity,
            buildings,
            1 if self.metropolis[0] else 0,
        ]

    def _water_to_binary(self):
        return [
            self._player_int,
            self.base_income,
            self.entity.quantity,
        ]

    def to_json(self):
        pass

    @property
    def _player_int(self):
        if self.owner:
            return self._player_to_int(self.owner)
        else:
            return 0

    @staticmethod
    def columns_names(type):
        if type == "island":
            return [
                "owner",
                "income",
                "num_of_entity",
                "building_1",
                "building_2",
                "building_3",
                "building_4",
                "metro"
            ]
        elif type == "water":
            return [
                "owner",
                "income",
                "num_of_entity"
            ]
        else:
            raise NotImplementedError
