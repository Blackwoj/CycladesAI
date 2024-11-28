from dataclasses import dataclass

from .AbstractDataClass import AbstractDataclass


@dataclass
class PlayerDataclass(AbstractDataclass):
    _player_id: str
    coins: int = 0
    philosophers: int = 0
    priests: int = 0

    def to_binary(self):
        return [
            self.coins,
            self.philosophers,
            self.priests
        ]

    @staticmethod
    def columns_names():
        return [
            "coins",
            "philosophers_cards",
            "priests_cards"
        ]
