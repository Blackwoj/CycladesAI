"""Pole planszy (wyspa lub woda). Odpowiednik game/dataclasses/FieldDataClass.py,
bez logiki binaryzacji i bez pól GUI.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Optional

from .entities import Building, Entity, Income
from .enums import FieldType


@dataclass
class Field:
    type: FieldType
    owner: Optional[str] = None          # "p1".. lub None
    base_income: int = 0
    entity: Entity = dc_field(default_factory=Entity)
    # miejsca pod budynki: slot_id -> Building | None (tylko wyspy)
    buildings: dict[str, Optional[Building]] = dc_field(default_factory=dict)
    is_metropolis: bool = False
    income: Income = dc_field(default_factory=Income)
    # sąsiedzi (id pól) — wypełniane przez layout planszy w Fazie 2
    neighbors: list[str] = dc_field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "owner": self.owner,
            "base_income": self.base_income,
            "entity": self.entity.to_dict(),
            "buildings": {
                slot: (b.to_dict() if b else None)
                for slot, b in self.buildings.items()
            },
            "is_metropolis": self.is_metropolis,
            "income": self.income.to_dict(),
            "neighbors": list(self.neighbors),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Field":
        return cls(
            type=FieldType(d["type"]),
            owner=d.get("owner"),
            base_income=d.get("base_income", 0),
            entity=Entity.from_dict(d.get("entity", {})),
            buildings={
                slot: (Building.from_dict(b) if b else None)
                for slot, b in d.get("buildings", {}).items()
            },
            is_metropolis=d.get("is_metropolis", False),
            income=Income.from_dict(d.get("income", {})),
            neighbors=list(d.get("neighbors", [])),
        )
