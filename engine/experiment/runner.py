"""ExperimentRunner — headless batch do pracy magisterskiej.

Uruchamia N gier, zbiera metryki porównawcze (LLM vs MCTS vs Random).
Gry mogą działać bez żadnego GUI ani importu pygame.

Przykład użycia:
    from engine.experiment.runner import ExperimentRunner, ExperimentConfig
    from engine.agents import RandomAgent
    from engine.rng import Rng

    config = ExperimentConfig(
        num_games=100,
        num_players=2,
        agents={"p1": RandomAgent(Rng(1)), "p2": RandomAgent(Rng(2))},
        seed=42,
        max_steps=500,
    )
    results = ExperimentRunner(config).run()
    print(results.summary())
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field as dc_field
from typing import Any

from ..agents.base import Agent
from ..engine import GameEngine
from ..rng import Rng
from ..state import GameState, Stage
from .telemetry import DecisionTrace, build_record


# ---------------------------------------------------------------------------
# Konfiguracja
# ---------------------------------------------------------------------------

@dataclass
class ExperimentConfig:
    num_games: int
    num_players: int
    agents: dict[str, Agent]                  # player_id -> agent
    seed: int | None = None
    max_steps: int = 1000                     # zabezpieczenie przed nieskończoną grą
    log_every: int = 0                        # co ile gier wypisać postęp (0 = cicho)
    matchup: str = ""                         # etykieta konfiguracji w telemetrii
    trace_path: str | None = None             # JSONL z jednym rekordem na decyzję


# ---------------------------------------------------------------------------
# Wynik pojedynczej gry
# ---------------------------------------------------------------------------

@dataclass
class GameResult:
    game_id: int
    winner: list[str]                         # [] jeśli remis lub przekroczono max_steps
    steps: int
    duration_ms: float
    illegal_moves: dict[str, int]             # player -> liczba odrzuconych akcji
    final_coins: dict[str, int]
    final_metropolis: dict[str, int]          # player -> liczba metropolii
    truncated: bool                           # True gdy przerwano przez max_steps

    def to_dict(self) -> dict:
        return {
            "game_id": self.game_id,
            "winner": self.winner,
            "steps": self.steps,
            "duration_ms": round(self.duration_ms, 2),
            "illegal_moves": self.illegal_moves,
            "final_coins": self.final_coins,
            "final_metropolis": self.final_metropolis,
            "truncated": self.truncated,
        }


# ---------------------------------------------------------------------------
# Zbiór wyników
# ---------------------------------------------------------------------------

@dataclass
class ExperimentResults:
    config: ExperimentConfig
    games: list[GameResult] = dc_field(default_factory=list)

    def summary(self) -> dict:
        total = len(self.games)
        if not total:
            return {"total": 0}

        win_counts: dict[str, int] = {}
        total_steps = 0
        total_illegal: dict[str, int] = {}
        truncated = 0

        for g in self.games:
            for w in g.winner:
                win_counts[w] = win_counts.get(w, 0) + 1
            total_steps += g.steps
            for pid, n in g.illegal_moves.items():
                total_illegal[pid] = total_illegal.get(pid, 0) + n
            if g.truncated:
                truncated += 1

        return {
            "total_games": total,
            "win_counts": win_counts,
            "win_rates": {p: round(n / total, 3) for p, n in win_counts.items()},
            "avg_steps": round(total_steps / total, 1),
            "total_illegal_moves": total_illegal,
            "illegal_rate": {
                p: round(n / total, 2) for p, n in total_illegal.items()
            },
            "truncated_games": truncated,
        }

    def to_jsonl(self) -> str:
        """Każda gra w osobnej linii JSON — wygodne do analizy."""
        import json
        return "\n".join(json.dumps(g.to_dict()) for g in self.games)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

class ExperimentRunner:
    def __init__(self, config: ExperimentConfig):
        self._cfg = config
        self._master_rng = Rng(config.seed)

    def run(self) -> ExperimentResults:
        results = ExperimentResults(config=self._cfg)
        with DecisionTrace(self._cfg.trace_path) as trace:
            for game_id in range(self._cfg.num_games):
                game_rng = self._master_rng.spawn()
                result = self._run_game(game_id, game_rng, trace)
                results.games.append(result)
                if self._cfg.log_every and (game_id + 1) % self._cfg.log_every == 0:
                    print(f"[experiment] gra {game_id + 1}/{self._cfg.num_games} — "
                          f"winner={result.winner}, steps={result.steps}")
        return results

    def _run_game(self, game_id: int, rng: Rng,
                  trace: "DecisionTrace | None" = None) -> GameResult:
        engine = GameEngine(rng=rng)
        state = engine.new_game(num_players=self._cfg.num_players, rng=rng.spawn())

        illegal: dict[str, int] = {pid: 0 for pid in state.players}
        t0 = time.monotonic()
        steps = 0

        while not engine.is_terminal(state) and steps < self._cfg.max_steps:
            if state.act_player is None:
                # Silnik w stanie przejściowym — przepchnij
                break

            agent = self._cfg.agents.get(state.act_player)
            if agent is None:
                break

            legal = engine.legal_actions(state)
            if not legal:
                break

            view = engine.state_view(state, state.act_player)
            t_dec = time.monotonic()
            try:
                chosen = agent.choose(view, legal)
            except Exception:
                # Agent rzucił wyjątkiem — licz jako nielegalny ruch, użyj pierwszej legalnej
                illegal[state.act_player] += 1
                chosen = legal[0]
            decision_ms = (time.monotonic() - t_dec) * 1000

            if trace is not None:
                trace.add(build_record(
                    matchup=self._cfg.matchup,
                    game_id=game_id,
                    step=steps,
                    state=state,
                    player=state.act_player,
                    agent=agent,
                    action=chosen,
                    decision_ms=decision_ms,
                    n_legal=len(legal),
                ))

            new_state, info = engine.step(state, chosen)
            if not info.get("valid", True):
                illegal[state.act_player] += 1
                # Wykonaj pierwszy legalny ruch zamiast
                if legal:
                    new_state, _ = engine.step(state, legal[0])

            state = new_state
            steps += 1

        duration_ms = (time.monotonic() - t0) * 1000
        winners = engine.winner(state)
        metropolis = self._count_metropolis(state)

        return GameResult(
            game_id=game_id,
            winner=winners,
            steps=steps,
            duration_ms=duration_ms,
            illegal_moves=illegal,
            final_coins={pid: p.coins for pid, p in state.players.items()},
            final_metropolis=metropolis,
            truncated=(steps >= self._cfg.max_steps and not engine.is_terminal(state)),
        )

    @staticmethod
    def _count_metropolis(state: GameState) -> dict[str, int]:
        from ..state import FieldType
        counts: dict[str, int] = {pid: 0 for pid in state.players}
        for field in state.fields.values():
            if field.type == FieldType.ISLAND and field.is_metropolis and field.owner in counts:
                counts[field.owner] += 1
        return counts
