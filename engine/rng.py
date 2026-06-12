"""Seedable RNG wrapper.

Wszystkie losowe decyzje silnika (kolejność graczy, dobór herosów, wynik walki)
przechodzą przez ten obiekt. Dzięki jawnemu seedowi:

- eksperymenty są reprodukowalne (ten sam seed => ten sam przebieg),
- MCTS może sterować losowością (determinizacja / chance nodes).
"""
from __future__ import annotations

import random
from typing import Sequence, TypeVar

T = TypeVar("T")


class Rng:
    def __init__(self, seed: int | None = None):
        self._seed = seed
        self._random = random.Random(seed)

    @property
    def seed(self) -> int | None:
        return self._seed

    def shuffle(self, items: list) -> None:
        self._random.shuffle(items)

    def choice(self, items: Sequence[T]) -> T:
        return self._random.choice(items)

    def randint(self, a: int, b: int) -> int:
        return self._random.randint(a, b)

    def random(self) -> float:
        return self._random.random()

    def spawn(self) -> "Rng":
        """Niezależny strumień (np. na pojedynczy rollout MCTS)."""
        return Rng(self._random.randint(0, 2**31 - 1))
