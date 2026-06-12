"""Losowy agent — baseline do porównań i do testów pętli rozgrywki."""
from __future__ import annotations

from ..actions import Action
from ..rng import Rng
from .base import Agent


class RandomAgent(Agent):
    def __init__(self, rng: Rng | None = None):
        self._rng = rng or Rng()

    def choose(self, state_view: dict, legal_actions: list[Action]) -> Action:
        if not legal_actions:
            raise ValueError("RandomAgent dostał pustą listę legalnych akcji")
        return self._rng.choice(legal_actions)
