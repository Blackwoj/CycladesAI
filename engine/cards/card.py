"""SZEW pod moduł kart specjalnych (Faza 7) — największy brakujący element gry.

Idea: silnik woła hooki rejestru, nie znając konkretnych kart. Dodanie nowej karty
to nowa klasa implementująca `Card` + `CARDS.register(...)`, BEZ zmian w rdzeniu
silnika. Na razie rejestr jest pusty — istnieje, by `legal_actions`/`step` mogły
już teraz pytać o karty (no-op), a serializacja stanu miała gdzie trzymać `cards`.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

# importy tylko do typowania; brak zależności od pygame
from ..state import GameState


@runtime_checkable
class Card(Protocol):
    """Kontrakt pojedynczej karty specjalnej."""
    card_id: str
    cost: int

    def is_playable(self, state: GameState, player: str) -> bool:
        ...

    def apply(self, state: GameState, player: str, targets: tuple) -> None:
        """Zmodyfikuj stan (in place na kopii, którą poda silnik)."""
        ...


class CardRegistry:
    def __init__(self):
        self._cards: dict[str, Card] = {}

    def register(self, card: Card) -> None:
        self._cards[card.card_id] = card

    def get(self, card_id: str) -> Card | None:
        return self._cards.get(card_id)

    def all(self) -> list[Card]:
        return list(self._cards.values())

    def playable_for(self, state: GameState, player: str) -> list[Card]:
        return [c for c in self._cards.values() if c.is_playable(state, player)]


# globalny, ale jawnie przekazywalny rejestr (silnik dostaje go w konstruktorze)
CARDS = CardRegistry()
