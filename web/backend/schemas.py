from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentSpec(BaseModel):
    kind: Literal["human", "random", "mcts", "llm"] = "human"
    n_simulations: int = Field(default=200, ge=1, le=5000)
    # tylko dla kind="llm"
    provider: Literal["anthropic", "openai", "gemini", "ollama"] = "anthropic"
    model: str | None = None          # None = domyślny model dostawcy
    mode: Literal["guided", "free_form"] = "guided"


class NewGameRequest(BaseModel):
    num_players: int = Field(default=2, ge=2, le=5)
    seed: int | None = None
    combat_dice: bool = False          # bitwy z kośćmi (oryginał) zamiast deterministycznych
    creatures: bool = True             # Mitologiczne Stwory
    # player_id -> spec; brakujący gracz = człowiek
    agents: dict[str, AgentSpec] = Field(default_factory=dict)


class StepRequest(BaseModel):
    # pełny dict akcji skopiowany z legal_actions (nie indeks — patrz FRONTEND.md §9.2)
    action: dict[str, Any]


class LogEntry(BaseModel):
    step: int
    round_no: int
    player: str
    hero: str | None
    action: dict[str, Any]
    info: dict[str, Any]
    decision_ms: float | None = None
    detail: dict[str, Any] = Field(default_factory=dict)   # telemetria agenta (tokeny, uzasadnienie LLM, ...)


class GameView(BaseModel):
    game_id: str
    seed: int
    step: int
    state: dict[str, Any]
    legal_actions: list[dict[str, Any]]
    act_player: str | None
    act_player_is_human: bool
    players: dict[str, str]          # player_id -> opis (Człowiek / MCTS (200) / ...)
    stage: str
    terminal: bool
    winners: list[str]
    info: dict[str, Any] = Field(default_factory=dict)
    log: list[LogEntry] = Field(default_factory=list)
