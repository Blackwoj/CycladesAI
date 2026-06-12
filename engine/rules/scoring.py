"""Warunki końca gry, dochód i przejście między rundami.

Port logiki z PrepareStageManager.end_stage(), calculate_income() i check_win().
"""
from __future__ import annotations

import copy

from ..rng import Rng
from ..state import FieldType, GameState, Stage
from .roll import setup_roll_phase

_WIN_METROPOLIS_COUNT = 2


# ---------------------------------------------------------------------------
# Dochód
# ---------------------------------------------------------------------------

def calculate_income(state: GameState) -> dict[str, int]:
    """Oblicz dochód każdego gracza (base_income + income żetony Apollona)."""
    income: dict[str, int] = {pid: 0 for pid in state.players}
    for field in state.fields.values():
        owner = field.owner
        if owner and owner in income:
            income[owner] += field.base_income
            income[owner] += field.income.quantity
    return income


# ---------------------------------------------------------------------------
# Warunek zwycięstwa
# ---------------------------------------------------------------------------

def check_winners(state: GameState) -> list[str]:
    """Zwróć listę graczy posiadających >= 2 metropolie."""
    metro_count: dict[str, int] = {}
    for field in state.fields.values():
        if field.type == FieldType.ISLAND and field.is_metropolis and field.owner:
            metro_count[field.owner] = metro_count.get(field.owner, 0) + 1
    return [p for p, n in metro_count.items() if n >= _WIN_METROPOLIS_COUNT]


def is_game_over(state: GameState) -> bool:
    return bool(check_winners(state)) or state.stage == Stage.GAME_OVER


# ---------------------------------------------------------------------------
# Koniec rundy — przejście BOARD → ROLL
# ---------------------------------------------------------------------------

def end_board_phase(state: GameState, rng: Rng) -> GameState:
    """Zakończ fazę BOARD: wypłać dochód, sprawdź wygraną, przejdź do ROLL."""
    s = copy.deepcopy(state)

    # Wypłata dochodu
    income = calculate_income(s)
    for pid, amount in income.items():
        s.players[pid].coins += amount

    # Sprawdź wygraną
    winners = check_winners(s)
    if winners:
        s.stage = Stage.GAME_OVER
        return s

    # Nowa runda
    s.round_no += 1
    s.act_player = None
    s.act_hero = None
    s.hero_players = {pid: "None" for pid in s.players}

    # Przywróć kolejność licytacji z wyników poprzedniej aukcji
    prev_bids = s.roll.bids
    bid_order = []
    for row, bid in prev_bids.items():
        if row == "row_5":
            bid_order.extend(bid)
        elif bid:
            bid_order.append(bid["player"])
    s.roll.bid_order = bid_order

    s = setup_roll_phase(s, rng)
    return s
