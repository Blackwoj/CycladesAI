"""Inicjalizacja planszy — tworzenie GameState z konfiguracji JSON.

Odpowiednik PrepareStageManager.setup_board_first_stage() z game/managers,
bez pygame. Dane planszy wczytywane z oryginalnych plików JSON ze starego kodu
(game/gui/common/config_section/boards/). Silnik nie kopiuje tych plików —
wskazuje na nie przez ścieżkę; jeśli kiedyś odepniemy pygame w pełni, dane
można przenieść do engine/data/.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from ..rng import Rng
from ..state import (
    Building,
    CardState,
    Entity,
    Field,
    FieldType,
    GameState,
    Income,
    Player,
    RollState,
    Stage,
)

_BOARDS_DIR = Path(__file__).resolve().parents[2] / "game" / "gui" / "common" / "config_section" / "boards"

HEROES_BIDDABLE = ["ares", "atena", "posejdon", "zeus"]

# koszt kolejnego wojownika Aresa: indeks = ile już wystawiono w tej turze
WARRIOR_PRICING = [0, 2, 3, 4]
# koszt kolejnego statku Posejdona
SHIP_PRICING = [0, 1, 2, 3]


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_board_data(num_players: int) -> tuple[dict, dict]:
    """Zwraca (water_config, islands_config) dla podanej liczby graczy.

    Oryginalne pliki JSON istnieją tylko dla 5 graczy. Dla mniejszej liczby
    graczy używamy tej samej planszy i ograniczamy liczbę aktywnych graczy —
    układ pól jest identyczny, zmienia się tylko who owns what na starcie.
    TODO (Faza 2+): dodać osobne JSONy dla 2–4 graczy.
    """
    available = [5]  # pliki które faktycznie istnieją
    n = num_players if num_players in available else 5
    water = _load_json(_BOARDS_DIR / "base_fileds_value" / f"water_{n}.json")
    islands = _load_json(_BOARDS_DIR / "base_fileds_value" / f"island_{n}.json")
    return water, islands


def build_initial_state(num_players: int, rng: Rng | None = None) -> GameState:
    """Zbuduj pełny stan początkowy z layoutem planszy."""
    if not 2 <= num_players <= 5:
        raise ValueError("Cyclades: 2-5 graczy")

    rng = rng or Rng()
    water_cfg, islands_cfg = load_board_data(num_players)

    fields: dict[str, Field] = {}

    # Pola wodne
    for field_id, cfg in water_cfg.items():
        owner, entity = _parse_owner_entity(cfg.get("owner", {}), "ship")
        neighbors = list(cfg.get("neighbors", [])) + list(cfg.get("neighbors_island", []))
        # Wyfiltruj ewentualne puste stringi (neighbors_island: "" w JSON)
        neighbors = [n for n in neighbors if n]
        fields[field_id] = Field(
            type=FieldType.WATER,
            owner=owner,
            base_income=cfg.get("base_income", 0),
            entity=entity,
            neighbors=neighbors,
        )

    # Wyspy
    for field_id, cfg in islands_cfg.items():
        owner, entity = _parse_owner_entity(cfg.get("owner", {}), "warrior")
        # Sąsiedzi wyspy = pola wodne, które mają tę wyspę w neighbors_island
        island_neighbors = [
            wid for wid, wcfg in water_cfg.items()
            if field_id in wcfg.get("neighbors_island", [])
        ]
        building_slots = {slot: None for slot in cfg["buildings"]["small"]}
        fields[field_id] = Field(
            type=FieldType.ISLAND,
            owner=owner,
            base_income=cfg.get("base_income", 0),
            entity=entity,
            buildings=building_slots,
            is_metropolis=False,
            income=Income(0),
            neighbors=island_neighbors,
        )

    players = _build_players(num_players)

    return GameState(
        num_of_players=num_players,
        stage=Stage.ROLL,
        round_no=1,
        players=players,
        fields=fields,
        hero_players={pid: "None" for pid in players},
        roll=RollState(
            heros_per_row={f"row_{i}": "" for i in range(1, 6)},
        ),
        cards=CardState(hands={pid: [] for pid in players}),
    )


def _parse_owner_entity(owner_dict: dict, entity_kind: str) -> tuple[str | None, Entity]:
    if not owner_dict:
        return None, Entity()
    player, quantity = next(iter(owner_dict.items()))
    return player, Entity(kind=entity_kind, quantity=quantity)


def _build_players(num_players: int) -> dict[str, Player]:
    # Startowe monety: p1-p3 = 5, p4 = 10, p5 = 10, 2 filozofów
    # (parytet z PlayerCache w grze oryginalnej)
    config = {
        "p1": Player("p1", coins=5),
        "p2": Player("p2", coins=5),
        "p3": Player("p3", coins=5),
        "p4": Player("p4", coins=10),
        "p5": Player("p5", coins=10, philosophers=2),
    }
    return {f"p{i}": config[f"p{i}"] for i in range(1, num_players + 1)}
