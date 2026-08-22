"""Telemetria decyzji — surowe dane do analizy i wykresów w pracy magisterskiej.

`ExperimentRunner` zbiera metryki zagregowane na poziomie GRY (kto wygrał, ile
kroków). Do wykresów to za mało: nie da się z tego pokazać, jak zmienia się
koszt decyzji w trakcie partii ani porównać trybu GUIDED z FREE_FORM pod kątem
liczby odrzuconych odpowiedzi. Ten moduł zapisuje **jeden rekord na decyzję**.

Zasada: agent nie wie o istnieniu telemetrii. Wystawia tylko `last_decision`
(dict, opcjonalny) i to runner decyduje, czy i gdzie to zapisać.

Format wyjściowy: JSONL — jedna decyzja w linii, strumieniowo, bez trzymania
całego przebiegu w pamięci. Analizę robi `engine/experiments/analyze.py`.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field as dc_field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Pojedyncza decyzja
# ---------------------------------------------------------------------------

@dataclass
class DecisionRecord:
    """Jedna decyzja jednego agenta w jednym kroku gry."""

    # --- identyfikacja przebiegu ---
    matchup: str = ""            # np. "llm_anthropic_guided_vs_random"
    game_id: int = 0
    step: int = 0

    # --- kontekst gry ---
    round_no: int = 0
    stage: str = ""              # roll | board
    player: str = ""
    hero: str = ""               # heros aktywny w tej turze

    # --- kto decydował ---
    agent_kind: str = ""         # random | mcts | llm | human
    agent_label: str = ""        # klasa agenta, np. AnthropicLLMAgent
    model: str = ""              # tylko LLM
    mode: str = ""               # guided | free_form (tylko LLM)

    # --- decyzja ---
    n_legal: int = 0             # rozmiar przestrzeni wyboru
    action_type: str = ""        # place_entity | move_entity | build | ...
    action: dict = dc_field(default_factory=dict)
    decision_ms: float = 0.0

    # --- koszt LLM ---
    input_tokens: int = 0
    output_tokens: int = 0
    illegal_attempts: int = 0    # odrzucone odpowiedzi w TEJ decyzji
    fallback_used: bool = False  # agent nie trafił i wylosowano akcję

    # --- praca MCTS ---
    simulations: int = 0
    tree_depth: float = 0.0

    # --- stan gracza w chwili decyzji (do wykresów postępu partii) ---
    coins: int = 0
    islands_owned: int = 0
    metropolis: int = 0
    warriors: int = 0
    ships: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Zapis strumieniowy
# ---------------------------------------------------------------------------

class DecisionTrace:
    """Bufor + zapis JSONL. Użycie jako context manager gwarantuje flush.

        with DecisionTrace("results/trace.jsonl") as trace:
            trace.add(record)
    """

    def __init__(self, path: str | Path | None):
        self.path = Path(path) if path else None
        self.records: list[DecisionRecord] = []
        self._fh = None
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = open(self.path, "w", encoding="utf-8")

    def add(self, record: DecisionRecord) -> None:
        self.records.append(record)
        if self._fh:
            self._fh.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def close(self) -> None:
        if self._fh:
            self._fh.close()
            self._fh = None

    def __enter__(self) -> "DecisionTrace":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Odczyt informacji z agenta i ze stanu
# ---------------------------------------------------------------------------

def agent_kind(agent: Any) -> str:
    """Rozpoznaj rodzaj agenta bez importowania jego klasy (unikamy cykli)."""
    name = type(agent).__name__
    if name == "RandomAgent":
        return "random"
    if name == "MCTSAgent":
        return "mcts"
    if name == "ConsoleHumanAgent":
        return "human"
    if name.endswith("LLMAgent"):
        return "llm"
    return name.lower()


def read_last_decision(agent: Any) -> dict:
    """Pobierz szczegóły ostatniej decyzji, jeśli agent je wystawia.

    Agenci bez telemetrii (RandomAgent) po prostu nie mają tego atrybutu —
    zwracamy pusty dict zamiast wymuszać wspólny interfejs.
    """
    data = getattr(agent, "last_decision", None)
    return dict(data) if isinstance(data, dict) else {}


def player_snapshot(state: Any, player_id: str) -> dict:
    """Policz zasoby gracza w chwili decyzji — surowiec pod wykresy postępu."""
    from ..state import FieldType

    p = state.players.get(player_id)
    islands = warriors = ships = metro = 0
    for f in state.fields.values():
        if f.owner != player_id:
            continue
        if f.type == FieldType.ISLAND:
            islands += 1
            warriors += f.entity.quantity
            if f.is_metropolis:
                metro += 1
        else:
            ships += f.entity.quantity
    return {
        "coins": p.coins if p else 0,
        "islands_owned": islands,
        "metropolis": metro,
        "warriors": warriors,
        "ships": ships,
    }


def build_record(
    *,
    matchup: str,
    game_id: int,
    step: int,
    state: Any,
    player: str,
    agent: Any,
    action: Any,
    decision_ms: float,
    n_legal: int,
) -> DecisionRecord:
    """Złóż rekord z kontekstu gry i tego, co zaraportował agent."""
    detail = read_last_decision(agent)
    snap = player_snapshot(state, player)
    return DecisionRecord(
        matchup=matchup,
        game_id=game_id,
        step=step,
        round_no=getattr(state, "round_no", 0),
        stage=getattr(getattr(state, "stage", None), "value", ""),
        player=player,
        hero=getattr(state, "act_hero", "") or "",
        agent_kind=agent_kind(agent),
        agent_label=type(agent).__name__,
        model=str(detail.get("model", "")),
        mode=str(detail.get("mode", "")),
        n_legal=n_legal,
        action_type=getattr(action, "type", ""),
        action=action.to_dict() if hasattr(action, "to_dict") else {},
        decision_ms=round(decision_ms, 2),
        input_tokens=int(detail.get("input_tokens", 0)),
        output_tokens=int(detail.get("output_tokens", 0)),
        illegal_attempts=int(detail.get("illegal_attempts", 0)),
        fallback_used=bool(detail.get("fallback_used", False)),
        simulations=int(detail.get("simulations", 0)),
        tree_depth=float(detail.get("tree_depth", 0.0)),
        **snap,
    )
