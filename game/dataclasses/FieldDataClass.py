from dataclasses import dataclass
from typing import Optional

from .BuildingDataClass import Building
from .EntitiesDataClass import Entity
from .IncomeDataClass import Income


@dataclass
class Field:
    type: str
    owner: str
    quantity: int
    base_income: int
    small_building: Optional[dict[str, str]] = None
    metropolis: bool = False
    income: int = 0


@dataclass
class Fieldv2:
    type: str
    owner: str
    base_income: int = 0
    entity: Entity = Entity(None, None, 0)
    buildings: Optional[dict[str, Optional[Building]]] = None
    metropolis: bool = False
    income: Income = Income(0, 2)

    def to_binary(self):
        pass

    def to_json(self):
        pass
