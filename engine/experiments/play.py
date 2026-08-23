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
import time
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


def _fmt_action(action) -> str:
    """Jedna linia opisu akcji — czytelna dla człowieka, nie dict."""
    a = action.to_dict()
    t = a.get("type")
    if t == "roll_bid":
        return f"licytuje {a['row']} za {a['amount']}"
    if t == "apollon_bid":
        return "dołącza do Apollona"
    if t == "place_entity":
        kind = "wojownika" if a["kind"] == "warrior" else "statek"
        return f"wystawia {kind} na {a['field_id']}"
    if t == "move_entity":
        return f"przesuwa {a['quantity']} z {a['from_field']} na {a['to_field']}"
    if t == "build":
        return f"buduje {a['hero']} na {a['field_id']}"
    if t == "buy_card":
        return f"kupuje kartę {a['hero']}"
    if t == "end_turn":
        return "kończy turę"
    return str(a)


def _log_step(steps: int, state, action, info, legal_count: int, ms: float) -> None:
    """Log jednego ruchu: kto, czym, co zrobił, z ilu opcji."""
    hero = state.act_hero or "-"
    p = state.players[state.act_player]
    line = (f"[r{state.round_no:>2} k{steps:>3}] {state.act_player} "
            f"({hero:<8} {p.coins:>2}zł) {_fmt_action(action):<34} "
            f"| {legal_count:>3} opcji | {ms:>6.0f} ms")
    if info.get("combat"):
        line += f" | WALKA -> {info.get('winner')}"
    if not info.get("valid", True):
        line += f" | ODRZUCONE: {info.get('reason')}"
    print(line, flush=True)


def play_interactive(
    agents: dict,
    num_players: int = 2,
    seed: int = 42,
    max_steps: int = 1000,
    log_moves: bool = False,
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
        t0 = time.monotonic()
        action = agent.choose(view, legal)
        decision_ms = (time.monotonic() - t0) * 1000
        prev = state
        state, info = engine.step(state, action)
        steps += 1

        if log_moves:
            _log_step(steps, prev, action, info, len(legal), decision_ms)

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
    parser.add_argument("--watch", action="store_true",
                        help="AI vs AI z logiem każdego ruchu (bez człowieka)")
    parser.add_argument("--max-steps", type=int, default=1000)
    args = parser.parse_args()

    # Tryb podglądu: dwa MCTS grają same, log ruch po ruchu.
    if args.watch:
        print(f"\nPODGLĄD: MCTS({args.mcts_sims}) vs MCTS({args.mcts_sims})")
        play_interactive(
            agents={"p1": MCTSAgent(n_simulations=args.mcts_sims, rollout_rng=Rng(99)),
                    "p2": MCTSAgent(n_simulations=args.mcts_sims, rollout_rng=Rng(77))},
            seed=args.seed,
            max_steps=args.max_steps,
            log_moves=True,
        )
        return

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
