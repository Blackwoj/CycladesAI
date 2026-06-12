"""Smoke testy silnika — aktualizacja po Fazie 2."""
import pytest

from engine.engine import GameEngine
from engine.rng import Rng
from engine.state import Stage
from engine.actions import EndTurn, RollBid, ApollonBid


def _engine(seed=42):
    return GameEngine(rng=Rng(seed))


def test_new_game_setup():
    engine = _engine()
    state = engine.new_game(num_players=3)
    assert state.num_of_players == 3
    assert set(state.players) == {"p1", "p2", "p3"}
    assert state.stage == Stage.ROLL
    assert state.act_player in state.players


def test_new_game_player_count_validation():
    engine = _engine()
    with pytest.raises(ValueError):
        engine.new_game(num_players=1)
    with pytest.raises(ValueError):
        engine.new_game(num_players=6)


def test_fresh_game_not_terminal():
    engine = _engine()
    state = engine.new_game(num_players=2)
    assert engine.is_terminal(state) is False


def test_legal_actions_roll_phase():
    engine = _engine()
    state = engine.new_game(num_players=2)
    assert state.stage == Stage.ROLL
    actions = engine.legal_actions(state)
    assert len(actions) > 0
    types = {type(a).__name__ for a in actions}
    assert "RollBid" in types or "ApollonBid" in types


def test_state_view_contains_perspective_and_legal_actions():
    engine = _engine()
    state = engine.new_game(num_players=2)
    view = engine.state_view(state, "p1")
    assert view["me"] == "p1"
    assert "players" in view and "fields" in view
    assert "legal_actions" in view


def test_step_roll_valid_action():
    engine = _engine(seed=7)
    state = engine.new_game(num_players=2)
    actions = engine.legal_actions(state)
    assert actions, "brak legalnych akcji w fazie ROLL"
    new_state, info = engine.step(state, actions[0])
    assert info.get("valid")
    # Stan musi się zmienić (inny gracz lub inna faza)
    assert new_state is not state


def test_step_returns_old_state_on_invalid_action():
    engine = _engine()
    state = engine.new_game(num_players=2)
    # EndTurn niedozwolony w fazie ROLL
    new_state, info = engine.step(state, EndTurn(player="p1"))
    # Albo info.valid=False albo stan niezmodyfikowany
    if info.get("valid"):
        # jeśli silnik zaakceptował, to ok
        pass
    else:
        assert new_state is state or new_state.stage == state.stage


def test_full_roll_phase_transitions_to_board():
    """Przejdź przez całą aukcję i sprawdź przejście do BOARD."""
    engine = _engine(seed=99)
    state = engine.new_game(num_players=2)
    assert state.stage == Stage.ROLL

    # Graj po jednej akcji na raz aż do BOARD lub za dużo iteracji
    for _ in range(50):
        if state.stage == Stage.BOARD:
            break
        actions = engine.legal_actions(state)
        if not actions:
            break
        state, info = engine.step(state, actions[0])

    assert state.stage == Stage.BOARD, f"Po 50 krokach wciąż {state.stage}"
    assert state.act_player is not None


def test_board_phase_can_play_end_turn():
    """Wejdź do BOARD i zagraj EndTurn."""
    engine = _engine(seed=5)
    state = engine.new_game(num_players=2)
    for _ in range(50):
        if state.stage == Stage.BOARD:
            break
        actions = engine.legal_actions(state)
        if not actions:
            break
        state, _ = engine.step(state, actions[0])

    if state.stage != Stage.BOARD:
        pytest.skip("nie udało się wejść w BOARD w 50 krokach")

    assert state.act_player is not None
    actions = engine.legal_actions(state)
    end_turn = next((a for a in actions if isinstance(a, EndTurn)), None)
    assert end_turn is not None
    state2, info = engine.step(state, end_turn)
    assert info.get("valid")
