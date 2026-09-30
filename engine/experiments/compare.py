"""Skrypt porównawczy do pracy magisterskiej.

Uruchamia serię gier między agentami i zapisuje wyniki do JSONL.

Użycie:
    python3 engine/experiments/compare.py                  # baseline + LLM (gdzie są klucze)
    python3 engine/experiments/compare.py --dry-run        # pokaż plan, bez gier i kosztów
    python3 engine/experiments/compare.py --skip-baseline --providers anthropic --llm-games 3

Matchupy LLM vs Random uruchamiają się same dla każdego dostawcy, który ma
pakiet SDK i klucz w .env (Ollama: działający serwer):
    cp .env.example .env && nano .env

Wyniki zapisywane do: engine/experiments/results/
"""
from __future__ import annotations

import argparse
import json
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
from engine.agents.llm_factory import PROVIDERS, make_llm_agent, provider_available
from engine.experiment.runner import ExperimentConfig, ExperimentRunner
from engine.rng import Rng


# ---------------------------------------------------------------------------
# Konfiguracja eksperymentów
# ---------------------------------------------------------------------------

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

N_GAMES = 20          # liczba gier na parę agentów
N_LLM_GAMES = 10      # mniej gier dla LLM — każda partia to ~200 płatnych wywołań
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
    slug = name.replace(" ", "_").lower()
    config = ExperimentConfig(
        num_games=n_games,
        num_players=N_PLAYERS,
        agents=agents,
        seed=SEED,
        max_steps=MAX_STEPS,
        log_every=5,
        matchup=slug,
        # Jeden rekord na decyzję — materiał pod analyze.py i wykresy.
        trace_path=str(RESULTS_DIR / "traces" / f"{slug}.jsonl"),
    )
    print(f"\n{'='*60}")
    print(f"  Matchup: {name}  ({n_games} gier)")
    print(f"{'='*60}")

    results = ExperimentRunner(config).run()
    summary = results.summary()

    # Zapisz wyniki do JSONL
    out_file = RESULTS_DIR / f"{slug}.jsonl"
    out_file.write_text(results.to_jsonl())
    print(f"  Zapisano: {out_file}")
    print(f"  Win rates: {summary['win_rates']}")
    print(f"  Avg steps: {summary['avg_steps']}")
    print(f"  Truncated: {summary['truncated_games']}/{n_games}")

    return {"name": name, **summary}


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Porównanie agentów Cyclades")
    ap.add_argument("--skip-baseline", action="store_true",
                    help="pomiń Random/MCTS (np. gdy baseline jest już policzony)")
    ap.add_argument("--games", type=int, default=N_GAMES, help="gier na matchup bazowy")
    ap.add_argument("--llm-games", type=int, default=N_LLM_GAMES, help="gier na matchup LLM")
    ap.add_argument("--providers", default=",".join(PROVIDERS),
                    help="dostawcy LLM do sprawdzenia, np. anthropic,ollama")
    ap.add_argument("--modes", default="guided,free_form", help="tryby LLM: guided,free_form")
    ap.add_argument("--dry-run", action="store_true",
                    help="tylko pokaż, co zostałoby uruchomione (bez gier i bez kosztów API)")
    return ap.parse_args()


def main() -> None:
    args = _parse_args()
    summaries = []
    plan: list[tuple[str, dict, int]] = []

    if not args.skip_baseline:
        plan += [
            ("random_vs_random", {"p1": RandomAgent(Rng(1)), "p2": RandomAgent(Rng(2))}, args.games),
            ("mcts_vs_random", {"p1": MCTSAgent(n_simulations=MCTS_SIMS, rollout_rng=Rng(1)),
                                "p2": RandomAgent(Rng(2))}, args.games),
            ("mcts_vs_mcts", {"p1": MCTSAgent(n_simulations=MCTS_SIMS, rollout_rng=Rng(1)),
                              "p2": MCTSAgent(n_simulations=MCTS_SIMS, rollout_rng=Rng(2))}, args.games),
        ]

    # ---- LLM vs Random — każdy dostawca z kluczem / serwerem, każdy tryb ----
    # Dostawca bez klucza jest pomijany z komunikatem, nie wywraca przebiegu.
    for provider in [p.strip() for p in args.providers.split(",") if p.strip()]:
        ok, reason = provider_available(provider)
        if not ok:
            print(f"  [pomijam LLM {provider}] {reason}")
            continue
        model = PROVIDERS[provider][0]
        for mode in [m.strip() for m in args.modes.split(",") if m.strip()]:
            name = f"llm_{provider}_{mode}_vs_random"
            if args.dry_run:
                plan.append((name, {}, args.llm_games))
                continue
            agent = make_llm_agent(provider, model, mode, fallback_rng=Rng(1))
            plan.append((name, {"p1": agent, "p2": RandomAgent(Rng(2))}, args.llm_games))

    if args.dry_run:
        print("\nPlan (dry-run):")
        for name, _, n in plan:
            print(f"  {name}: {n} gier")
        return

    for name, agents, n in plan:
        summaries.append(run_matchup(name, agents, n_games=n))

    # ---- Zapis zbiorczego raportu -----------------------------------------
    # Scalanie po nazwie: przebieg samych LLM (--skip-baseline) nie kasuje baseline'u.
    report_file = RESULTS_DIR / "summary.json"
    merged = {}
    if report_file.exists():
        merged = {s["name"]: s for s in json.loads(report_file.read_text())}
    merged.update({s["name"]: s for s in summaries})
    report_file.write_text(json.dumps(list(merged.values()), indent=2))
    print(f"\nZbiorczy raport: {report_file}")
    print("\nWyniki:")
    for s in summaries:
        print(f"  {s['name']}: win_rates={s['win_rates']}, avg_steps={s['avg_steps']}")


if __name__ == "__main__":
    main()
