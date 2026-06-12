"""Skrypt porównawczy do pracy magisterskiej.

Uruchamia serię gier między agentami i zapisuje wyniki do JSONL.

Użycie:
    python3 engine/experiments/compare.py

Domyślnie uruchamia Random vs MCTS. Aby dodać LLMAgent, odkomentuj sekcję
LLM i ustaw zmienne środowiskowe w .env:
    cp .env.example .env && nano .env

Wyniki zapisywane do: engine/experiments/results/
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Upewnij się, że root projektu jest w PATH
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv opcjonalny

from engine.agents import MCTSAgent, RandomAgent
from engine.experiment.runner import ExperimentConfig, ExperimentRunner
from engine.rng import Rng


# ---------------------------------------------------------------------------
# Konfiguracja eksperymentów
# ---------------------------------------------------------------------------

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

N_GAMES = 20          # liczba gier na parę agentów
N_PLAYERS = 2
SEED = 42
MCTS_SIMS = 100       # symulacje MCTS — więcej = lepszy, ale wolniejszy

# Uwaga: silnik używa planszy dla 5 graczy dla wszystkich konfiguracji (brak osobnych
# plansz 2-4 graczy w oryginalnych danych). Gry 2-osobowe trwają dłużej (~600-800 kroków)
# bo plansza jest duża. max_steps=800 ogranicza czas; gry truncated są poprawną
# metryką do porównania (truncated% spada gdy agenci grają lepiej).
MAX_STEPS = 800


def run_matchup(name: str, agents: dict, n_games: int = N_GAMES) -> dict:
    """Uruchom jedną konfigurację i zwróć podsumowanie."""
    config = ExperimentConfig(
        num_games=n_games,
        num_players=N_PLAYERS,
        agents=agents,
        seed=SEED,
        max_steps=MAX_STEPS,
        log_every=5,
    )
    print(f"\n{'='*60}")
    print(f"  Matchup: {name}  ({n_games} gier)")
    print(f"{'='*60}")

    results = ExperimentRunner(config).run()
    summary = results.summary()

    # Zapisz wyniki do JSONL
    out_file = RESULTS_DIR / f"{name.replace(' ', '_').lower()}.jsonl"
    out_file.write_text(results.to_jsonl())
    print(f"  Zapisano: {out_file}")
    print(f"  Win rates: {summary['win_rates']}")
    print(f"  Avg steps: {summary['avg_steps']}")
    print(f"  Truncated: {summary['truncated_games']}/{n_games}")

    return {"name": name, **summary}


def main() -> None:
    summaries = []

    # ---- 1. Random vs Random (baseline) -----------------------------------
    summaries.append(run_matchup(
        "random_vs_random",
        {
            "p1": RandomAgent(Rng(1)),
            "p2": RandomAgent(Rng(2)),
        }
    ))

    # ---- 2. MCTS vs Random ------------------------------------------------
    summaries.append(run_matchup(
        "mcts_vs_random",
        {
            "p1": MCTSAgent(n_simulations=MCTS_SIMS, rollout_rng=Rng(1)),
            "p2": RandomAgent(Rng(2)),
        }
    ))

    # ---- 3. MCTS vs MCTS --------------------------------------------------
    summaries.append(run_matchup(
        "mcts_vs_mcts",
        {
            "p1": MCTSAgent(n_simulations=MCTS_SIMS, rollout_rng=Rng(1)),
            "p2": MCTSAgent(n_simulations=MCTS_SIMS, rollout_rng=Rng(2)),
        }
    ))

    # ---- 4. LLM (Anthropic) vs Random — odkomentuj gdy masz klucz ---------
    # anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    # if anthropic_key:
    #     from engine.agents import AnthropicLLMAgent, LLMMode
    #     summaries.append(run_matchup(
    #         "llm_anthropic_guided_vs_random",
    #         {
    #             "p1": AnthropicLLMAgent(
    #                 model="claude-haiku-4-5",
    #                 mode=LLMMode.GUIDED,
    #                 verbose=True,
    #             ),
    #             "p2": RandomAgent(Rng(2)),
    #         },
    #         n_games=10,  # mniej gier bo LLM jest kosztowny
    #     ))
    # else:
    #     print("\nBrak ANTHROPIC_API_KEY — pomijam matchup LLM vs Random")

    # ---- Zapis zbiorczego raportu -----------------------------------------
    report_file = RESULTS_DIR / "summary.json"
    report_file.write_text(json.dumps(summaries, indent=2))
    print(f"\nZbiorczy raport: {report_file}")
    print("\nWyniki:")
    for s in summaries:
        print(f"  {s['name']}: win_rates={s['win_rates']}, avg_steps={s['avg_steps']}")


if __name__ == "__main__":
    main()
