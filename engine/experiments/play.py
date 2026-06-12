"""Interaktywna gra człowiek vs AI — do demonstracji i testowania agentów.

Użycie:
    python3 engine/experiments/play.py              # człowiek vs MCTS
    python3 engine/experiments/play.py --llm        # człowiek vs Claude (wymaga .env)
    python3 engine/experiments/play.py --mcts-sims 500  # silniejszy MCTS

Sterowanie:
    Wpisz numer akcji i zatwierdź Enterem.
    Ctrl+C → automatycznie wybiera akcję [0] (EndTurn/pierwsza legalna).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from engine.agents import ConsoleHumanAgent, MCTSAgent, RandomAgent
from engine.engine import GameEngine
from engine.rng import Rng
from engine.state import Stage


def play_interactive(
    agents: dict,
    num_players: int = 2,
    seed: int = 42,
    max_steps: int = 1000,
) -> None:
    """Uruchom grę interaktywną z podanymi agentami."""
    rng = Rng(seed)
    engine = GameEngine(rng=rng)
    state = engine.new_game(num_players=num_players, rng=rng.spawn())

    print("\n" + "="*60)
    print("  CYCLADES — gra interaktywna")
    print(f"  Gracze: {list(agents.keys())}")
    print("="*60)

    steps = 0
    while not engine.is_terminal(state) and steps < max_steps:
        if state.act_player is None:
            break

        agent = agents.get(state.act_player)
        if agent is None:
            print(f"Brak agenta dla gracza {state.act_player}")
            break

        legal = engine.legal_actions(state)
        if not legal:
            break

        view = engine.state_view(state, state.act_player)
        action = agent.choose(view, legal)
        state, info = engine.step(state, action)
        steps += 1

        if info.get("winners"):
            break

    # Wynik
    print("\n" + "="*60)
    winners = engine.winner(state)
    if winners:
        print(f"  ZWYCIĘZCA: {winners}  (po {steps} krokach)")
    else:
        print(f"  Gra przerwana po {steps} krokach (max_steps={max_steps})")
    print("="*60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Cyclades — człowiek vs AI")
    parser.add_argument("--mcts-sims", type=int, default=200,
                        help="Liczba symulacji MCTS (domyślnie 200)")
    parser.add_argument("--llm", action="store_true",
                        help="Użyj LLM (Claude) zamiast MCTS jako AI")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    human = ConsoleHumanAgent(name="Ty (p1)")

    if args.llm:
        try:
            from engine.agents import AnthropicLLMAgent, LLMMode
            ai = AnthropicLLMAgent(model="claude-haiku-4-5", verbose=True)
            ai_label = "Claude (p2)"
        except Exception as e:
            print(f"Nie można załadować LLM ({e}), używam MCTS.")
            ai = MCTSAgent(n_simulations=args.mcts_sims, rollout_rng=Rng(99))
            ai_label = f"MCTS sims={args.mcts_sims} (p2)"
    else:
        ai = MCTSAgent(n_simulations=args.mcts_sims, rollout_rng=Rng(99))
        ai_label = f"MCTS sims={args.mcts_sims} (p2)"

    print(f"\nAI: {ai_label}")
    play_interactive(
        agents={"p1": human, "p2": ai},
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
