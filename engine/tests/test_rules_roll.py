"""Testy fazy ROLL — aukcja herosów."""
import pytest
from engine.rules.roll import (
    setup_roll_phase,
    legal_roll_actions,
    apply_roll_bid,
    apply_apollon_bid,
    finalize_roll,
)
from engine.rules.setup import build_initial_state
from engine.rng import Rng
from engine.state import Stage
from engine.actions import RollBid, ApollonBid


def _fresh(n=3, seed=42):
    state = build_initial_state(n, Rng(seed))
    return setup_roll_phase(state, Rng(seed))


def test_setup_roll_assigns_heroes():
    s = _fresh(n=3)
    active = {r: h for r, h in s.roll.heros_per_row.items() if h and r != "row_5"}
    # 3 graczy → 2 herosi (num_players - 1)
    assert len(active) == 2


def test_setup_roll_sets_act_player():
    s = _fresh()
    assert s.act_player in s.players


def test_legal_actions_returns_bids_and_apollon():
    s = _fresh()
    actions = legal_roll_actions(s)
    types = {type(a).__name__ for a in actions}
    assert "RollBid" in types or "ApollonBid" in types


def test_apply_roll_bid_advances_player():
    s = _fresh()
    actions = legal_roll_actions(s)
    bid_actions = [a for a in actions if isinstance(a, RollBid)]
    if not bid_actions:
        pytest.skip("brak legalnych licytacji — skip")
    first_player = s.act_player
    new_state = apply_roll_bid(s, bid_actions[0])
    # Po licytacji tura przeszła do kolejnego gracza (lub BOARD jeśli to był ostatni)
    assert new_state.act_player != first_player or new_state.stage == Stage.BOARD


def test_finalize_roll_creates_play_order():
    s = _fresh(n=2, seed=7)
    # Wymuszamy puste bid_order → finalize
    s.roll.bid_order = []
    # Ręcznie ustaw oferty
    players = list(s.players.keys())
    active_rows = [r for r, h in s.roll.heros_per_row.items() if h and r != "row_5"]
    if active_rows:
        s.roll.bids[active_rows[0]] = {"player": players[0], "bid": 2}
    s.roll.bids["row_5"] = [players[1]] if len(players) > 1 else []

    result = finalize_roll(s)
    assert result.stage == Stage.BOARD
    assert len(result.play_order) > 0


def test_finalize_roll_deducts_coins():
    s = _fresh(n=2, seed=3)
    players = list(s.players.keys())
    active_rows = [r for r, h in s.roll.heros_per_row.items() if h and r != "row_5"]
    if not active_rows:
        pytest.skip("brak aktywnych rzędów")
    s.roll.bid_order = []
    initial_coins = s.players[players[0]].coins
    s.roll.bids[active_rows[0]] = {"player": players[0], "bid": 3}
    result = finalize_roll(s)
    assert result.players[players[0]].coins < initial_coins


def test_apollon_bid_adds_to_row5():
    s = _fresh(n=3)
    player_id = s.act_player
    s.roll.bids["row_5"] = []
    new_state = apply_apollon_bid(s, ApollonBid(player=player_id))
    assert player_id in new_state.roll.bids["row_5"]
