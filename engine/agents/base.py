"""Interfejs agenta — jedyny punkt styku decydenta z silnikiem.

Każdy decydent (człowiek przez pygame, LLM, MCTS, losowy baseline) implementuje
ten sam kontrakt. Agent NIE widzi pełnego stanu wewnętrznego — dostaje projekcję
(`state_view`) i listę legalnych akcji, i zwraca jedną z nich.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..actions import Action


class Agent(ABC):
    @abstractmethod
    def choose(self, state_view: dict, legal_actions: list[Action]) -> Action:
        """Wybierz jedną akcję z `legal_actions`.

        :param state_view: projekcja stanu dla gracza (dict, serializowalny).
        :param legal_actions: niepusta lista dozwolonych akcji.
        """
        raise NotImplementedError
