"""Drobne elementy stanu pola: jednostki, budynki, dochód.

Odpowiedniki dataclass z game/dataclasses, ale BEZ pól GUI
(np. Building.gui_location), bo silnik jest headless.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Entity:
    """Stos jednostek na polu (wojownicy / statki)."""
    kind: Optional[str] = None   # "warrior" | "ship" | None
    quantity: int = 0

    def to_dict(self) -> dict:
        return {"kind": self.kind, "quantity": self.quantity}

    @classmethod
    def from_dict(cls, d: dict) -> "Entity":
        return cls(kind=d.get("kind"), quantity=d.get("quantity", 0))


@dataclass
class Building:
    """Budynek herosa na wyspie."""
    hero: str               # "ares" | "atena" | "posejdon" | "zeus"

    def to_dict(self) -> dict:
        return {"hero": self.hero}

    @classmethod
    def from_dict(cls, d: dict) -> "Building":
        return cls(hero=d["hero"])


@dataclass
class Income:
    """Dodatkowy dochód pola (żeton Apollona)."""
    quantity: int = 0

    def to_dict(self) -> dict:
        return {"quantity": self.quantity}

    @classmethod
    def from_dict(cls, d: dict) -> "Income":
        return cls(quantity=d.get("quantity", 0))
