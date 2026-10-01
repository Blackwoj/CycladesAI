"""Dochód, warunek zwycięstwa i przejście między cyklami (instrukcja str. 2, 6).

Przebieg cyklu: 1) tor Stworów, 2) bogowie, 3) dochód, 4) ofiary, 5) akcje.
Gra kończy się NA KONIEC cyklu, w którym ktoś ma wymagane Metropolie
(2; w grze 2-osobowej 3). Kilku takich graczy → wygrywa najbogatszy.
"""
from __future__ import annotations

import copy

from ..rng import Rng
from ..state import FieldType, GameState, Stage
from .roll import setup_roll_phase


# ---------------------------------------------------------------------------
# Dochód
# ---------------------------------------------------------------------------

def calculate_income(state: GameState) -> dict[str, int]:
    """1 GP za każdy znacznik dobrobytu: z wysp, pól handlu (morze) i Apolla."""
    income: dict[str, int] = {pid: 0 for pid in state.players}
    for field in state.fields.values():
        owner = field.owner
        if owner and owner in income:
            income[owner] += field.base_income
            income[owner] += field.income.quantity
    return income


def pay_income(state: GameState) -> None:
    """Wypłać dochód (mutuje stan)."""
    for pid, amount in calculate_income(state).items():
        state.players[pid].coins += amount


# ---------------------------------------------------------------------------
# Warunek zwycięstwa
# ---------------------------------------------------------------------------

def metro_counts(state: GameState) -> dict[str, int]:
    counts: dict[str, int] = {}
    for field in state.fields.values():
        if field.type == FieldType.ISLAND and field.is_metropolis and field.owner:
            counts[field.owner] = counts.get(field.owner, 0) + 1
    return counts


def check_winners(state: GameState) -> list[str]:
    """Kto spełnia warunek zwycięstwa teraz (remis rozstrzygnięty złotem)."""
    target = state.options.metros_to_win
    qualified = [p for p, n in metro_counts(state).items() if n >= target]
    if len(qualified) <= 1:
        return qualified
    best = max(state.players[p].coins for p in qualified)
    return sorted(p for p in qualified if state.players[p].coins == best)


def is_game_over(state: GameState) -> bool:
    return state.stage == Stage.GAME_OVER


# ---------------------------------------------------------------------------
# Początek cyklu
# ---------------------------------------------------------------------------

def start_cycle(state: GameState, rng: Rng) -> GameState:
    """Kroki 1–4 cyklu: tor Stworów, bogowie + kolejność ofiar, dochód (kopia)."""
    from .creatures import update_track
    s = copy.deepcopy(state)
    update_track(s, rng)
    s = setup_roll_phase(s, rng)
    pay_income(s)
    return s


# ---------------------------------------------------------------------------
# Koniec cyklu — przejście BOARD → ROLL
# ---------------------------------------------------------------------------

def end_board_phase(state: GameState, rng: Rng) -> GameState:
    """Koniec cyklu: sprawdź zwycięstwo, w przeciwnym razie zacznij nowy cykl."""
    s = copy.deepcopy(state)
    winners = check_winners(s)
    if winners:
        s.winners = winners
        s.stage = Stage.GAME_OVER
        s.act_player = None
        return s

    s.round_no += 1
    s.act_player = None
    s.act_hero = None
    s.hero_players = {pid: "None" for pid in s.players}
    s.round_heroes = {pid: [] for pid in s.players}
    return start_cycle(s, rng)
