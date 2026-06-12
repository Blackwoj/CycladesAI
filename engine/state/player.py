"""Gracz. Odpowiednik game/dataclasses/PlayerDataClass.py."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Player:
    player_id: str
    coins: int = 0
    philosophers: int = 0   # karty Ateny
    priests: int = 0        # karty Zeusa (zniżka w aukcji)

    def to_dict(self) -> dict:
        return {
            "player_id": self.player_id,
            "coins": self.coins,
            "philosophers": self.philosophers,
            "priests": self.priests,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Player":
        return cls(
            player_id=d["player_id"],
            coins=d.get("coins", 0),
            philosophers=d.get("philosophers", 0),
            priests=d.get("priests", 0),
        )
