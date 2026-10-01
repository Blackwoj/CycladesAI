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
    GameOptions,
    GameState,
    Income,
    Player,
    RollState,
    Stage,
)

_BOARDS_DIR = Path(__file__).resolve().parents[2] / "game" / "gui" / "common" / "config_section" / "boards"

HEROES_BIDDABLE = ["ares", "atena", "posejdon", "zeus"]

# koszt kolejnego wojownika Aresa: indeks = ile już wystawiono w tej turze.
# Instrukcja: 1. darmowy, potem 2/3/4 GP, maks. 3 dodatkowe na turę (4 łącznie).
WARRIOR_PRICING = [0, 2, 3, 4]
# koszt kolejnej floty Posejdona: 1. darmowa, potem 1/2/3 GP, maks. 4 na turę
SHIP_PRICING = [0, 1, 2, 3]
MAX_UNITS = 8           # na planszy, osobno Oddziały i Floty
START_COINS = 5

# Poprawki rozstawienia 5-osobowego z JSON-ów starego GUI. Instrukcja (str. 7):
# każdy gracz ma 2 wyspy, 2 Oddziały i 2 Floty. W JSON-ie p5 miał 3 wyspy,
# 6 Oddziałów i 4 Floty (dane testowe). Zgodnie z ilustracją zostawiamy p5
# wyspy IS4 + IS13 i Floty F5 + K6. Pliki w game/ zostają nietknięte.
_START_FIXES_5 = {
    "IS4": {"p5": 1},
    "IS8": {},
    "F6": {},
    "G7": {},
}


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


def build_initial_state(
    num_players: int, rng: Rng | None = None, options: GameOptions | None = None,
) -> GameState:
    """Zbuduj pełny stan początkowy z layoutem planszy."""
    if not 2 <= num_players <= 5:
        raise ValueError("Cyclades: 2-5 graczy")

    rng = rng or Rng()
    options = options or GameOptions()
    if num_players == 2 and options.metros_to_win == 2:
        options = GameOptions(**{**options.to_dict(), "metros_to_win": 3})
    water_cfg, islands_cfg = load_board_data(num_players)
    for fid, owner in _START_FIXES_5.items():
        cfg = water_cfg.get(fid) or islands_cfg.get(fid)
        cfg["owner"] = owner

    players = _build_players(num_players)
    # Pliki JSON opisują rozstawienie dla 5 graczy. Przy mniejszej liczbie
    # graczy pozycje p3/p4/p5 muszą zostać neutralne — inaczej na planszy
    # siedzą "gracze-widma": właściciele bez agenta, którzy nigdy się nie ruszą
    # ani nie stracą jednostek, a blokują ekspansję i zawyżają truncation.
    active_players = set(players)

    fields: dict[str, Field] = {}

    # Pola wodne
    for field_id, cfg in water_cfg.items():
        owner, entity = _parse_owner_entity(cfg.get("owner", {}), "ship", active_players)
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
        owner, entity = _parse_owner_entity(cfg.get("owner", {}), "warrior", active_players)
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
        cards=_initial_creatures(rng) if options.creatures else CardState(),
        options=options,
    )


def _initial_creatures(rng: Rng) -> CardState:
    from .creatures import CREATURES
    deck = list(CREATURES)
    rng.shuffle(deck)
    return CardState(deck=deck)


def _parse_owner_entity(
    owner_dict: dict,
    entity_kind: str,
    active_players: set[str] | None = None,
) -> tuple[str | None, Entity]:
    """Odczytaj właściciela i jednostki startowe pola z konfiguracji JSON.

    `active_players` ogranicza rozstawienie do graczy faktycznie biorących
    udział w partii; pozycje pozostałych zostają neutralne (bez właściciela
    i bez jednostek).
    """
    if not owner_dict:
        return None, Entity()
    player, quantity = next(iter(owner_dict.items()))
    if active_players is not None and player not in active_players:
        return None, Entity()
    return player, Entity(kind=entity_kind, quantity=quantity)


def _build_players(num_players: int) -> dict[str, Player]:
    # Instrukcja: każdy gracz dostaje 5 GP. (PlayerCache starego GUI dawał p4/p5
    # po 10 GP i p5 2 filozofów — dane testowe, nie zasada.)
    return {f"p{i}": Player(f"p{i}", coins=START_COINS) for i in range(1, num_players + 1)}
