"""ConsoleHumanAgent — gracz człowiek przez konsolę.

Wyświetla stan gry i listę legalnych akcji; czeka na wybór indeksu od użytkownika.
Używany do grania przeciwko MCTSAgent / LLMAgent z terminala.

Przykład:
    from engine.agents import ConsoleHumanAgent, MCTSAgent
    from engine.experiments.play import play_interactive

    play_interactive(human="p1", ai_agent=MCTSAgent(n_simulations=200))
"""
from __future__ import annotations

from ..actions import Action
from .base import Agent
from .llm_agent import _render_common, _action_summary


class ConsoleHumanAgent(Agent):
    """Agent człowiek — wybiera akcję z numerowanej listy w terminalu."""

    def __init__(self, name: str = "Człowiek") -> None:
        self.name = name

    def choose(self, state_view: dict, legal_actions: list[Action]) -> Action:
        self._print_state(state_view, legal_actions)

        while True:
            try:
                raw = input(f"\n[{self.name}] Wybierz akcję (0–{len(legal_actions)-1}): ").strip()
                idx = int(raw)
                if 0 <= idx < len(legal_actions):
                    chosen = legal_actions[idx]
                    print(f"  → {_action_summary(chosen.to_dict())}")
                    return chosen
                print(f"  Wpisz liczbę między 0 a {len(legal_actions)-1}.")
            except (ValueError, KeyboardInterrupt, EOFError):
                print("\n  (wybrano akcję [0] — EndTurn / pierwsza legalna)")
                return legal_actions[0]

    def _print_state(self, v: dict, legal_actions: list[Action]) -> None:
        lines = _render_common(v)
        lines.append("")
        lines.append("LEGALNE AKCJE:")
        for i, a in enumerate(legal_actions):
            lines.append(f"  [{i:2d}] {_action_summary(a.to_dict())}")
        print("\n" + "\n".join(lines))
