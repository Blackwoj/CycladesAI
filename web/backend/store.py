"""GameStore — partie trzymane w pamięci procesu.

Backend nie zna zasad gry: trzyma GameState, woła GameEngine i serializuje
wynik. Każdy krok jest też dopisywany do runs/{game_id}.jsonl (replay).
"""
from __future__ import annotations

import json
import random
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from engine.actions import Action
from engine.agents import Agent
from engine.engine import GameEngine
from engine.rng import Rng
from engine.state import GameOptions, GameState

from .agents_factory import build_agent, describe
from .schemas import AgentSpec

RUNS_DIR = Path(__file__).resolve().parent / "runs"
LOG_TAIL = 60


@dataclass
class Game:
    game_id: str
    seed: int
    engine: GameEngine
    state: GameState
    agents: dict[str, Agent]
    labels: dict[str, str]
    step: int = 0
    log: list[dict] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def is_human(self, player_id: str | None) -> bool:
        return player_id is not None and player_id not in self.agents

    def apply(self, action: Action, decision_ms: float | None = None, detail: dict | None = None) -> dict:
        prev = self.state
        self.state, info = self.engine.step(prev, action)
        if info.get("valid", True):
            self.step += 1
            entry = {
                "step": self.step,
                "round_no": prev.round_no,
                "player": action.to_dict().get("player") or prev.act_player,
                "hero": prev.act_hero,
                "action": action.to_dict(),
                "info": _jsonable(info),
                "decision_ms": decision_ms,
                "detail": _jsonable(detail or {}),
            }
            self.log.append(entry)
            _append_run(self.game_id, entry)
        return info


def _jsonable(info: dict) -> dict:
    return json.loads(json.dumps(info, default=str))


def _append_run(game_id: str, entry: dict) -> None:
    try:
        RUNS_DIR.mkdir(exist_ok=True)
        with open(RUNS_DIR / f"{game_id}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # replay to dodatek — nie blokuje gry


class GameStore:
    def __init__(self) -> None:
        self._games: dict[str, Game] = {}

    def create(
        self, num_players: int, seed: int | None, specs: dict[str, AgentSpec],
        options: GameOptions | None = None,
    ) -> Game:
        seed = seed if seed is not None else random.randint(0, 2**31 - 1)
        rng = Rng(seed)
        engine = GameEngine(rng=rng, options=options)
        state = engine.new_game(num_players, rng.spawn())

        agents: dict[str, Agent] = {}
        labels: dict[str, str] = {}
        for pid in state.players:
            spec = specs.get(pid, AgentSpec())
            agent = build_agent(spec, rng)
            if agent is not None:
                agents[pid] = agent
            labels[pid] = describe(spec)

        game = Game(uuid.uuid4().hex[:12], seed, engine, state, agents, labels)
        self._games[game.game_id] = game
        _append_run(game.game_id, {"event": "new_game", "seed": seed,
                                   "num_players": num_players, "players": labels,
                                   "options": state.options.to_dict(),
                                   "ts": time.time()})
        return game

    def get(self, game_id: str) -> Game | None:
        return self._games.get(game_id)


store = GameStore()
