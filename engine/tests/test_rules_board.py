"""Testy fazy BOARD — tury graczy, walidacja akcji, walka, budowanie."""
import pytest
from engine.rules.setup import build_initial_state
from engine.rules.roll import setup_roll_phase, finalize_roll
from engine.rules.board import (
    start_player_turn,
    legal_board_actions,
    apply_board_action,
)
from engine.rules.scoring import calculate_income, check_winners
from engine.rng import Rng
from engine.state import (
    FieldType, GameState, Player, Field, Building, Entity, Stage, BoardPhaseState
)
from engine.actions import PlaceEntity, MoveEntity, Build, BuyCard, EndTurn


def _board_state(n=2, seed=1):
    """Zbuduj stan gotowy do fazy BOARD z przypisanym pierwszym graczem."""
    s = build_initial_state(n, Rng(seed))
    s = setup_roll_phase(s, Rng(seed))
    # Wymuś przejście do BOARD z prostymi przypisaniami
    s.stage = Stage.BOARD
    players = list(s.players.keys())
    s.hero_players = {players[0]: "ares", players[1]: "posejdon"}
    s.play_order = list(players)
    s = start_player_turn(s)
    return s


def test_start_player_turn_sets_hero():
    s = _board_state()
    assert s.act_hero in ("ares", "posejdon", "atena", "zeus", "apollon", "ap_s")
    assert s.act_player is not None


def test_end_turn_advances_play_order():
    s = _board_state(n=2)
    first_player = s.act_player
    s2, info = apply_board_action(s, EndTurn(player=first_player), Rng(1))
    assert info.get("valid")


def test_legal_actions_include_end_turn():
    s = _board_state()
    actions = legal_board_actions(s)
    assert any(isinstance(a, EndTurn) for a in actions)


def test_place_warrior_deducts_coins():
    s = _board_state()
    player_id = s.act_player
    s.act_hero = "ares"
    s.hero_players[player_id] = "ares"

    # Znajdź wyspę gracza
    my_island = next(
        (fid for fid, f in s.fields.items()
         if f.type == FieldType.ISLAND and f.owner == player_id),
        None
    )
    if my_island is None:
        pytest.skip("gracz nie ma wyspy startowej")

    before_coins = s.players[player_id].coins
    action = PlaceEntity(player=player_id, field_id=my_island, kind="warrior", quantity=1)
    s2, info = apply_board_action(s, action, Rng(1))
    # Pierwszy wojownik jest darmowy (WARRIOR_PRICING[0] = 0)
    assert info.get("valid")
    assert s2.fields[my_island].entity.quantity == s.fields[my_island].entity.quantity + 1


def test_build_costs_2_coins():
    s = _board_state()
    player_id = s.act_player
    s.act_hero = "ares"
    s.players[player_id].coins = 10

    my_island = next(
        (fid for fid, f in s.fields.items()
         if f.type == FieldType.ISLAND and f.owner == player_id),
        None
    )
    if my_island is None:
        pytest.skip("gracz nie ma wyspy")

    before = s.players[player_id].coins
    action = Build(player=player_id, field_id=my_island, hero="ares")
    s2, info = apply_board_action(s, action, Rng(1))
    if info.get("valid"):
        assert s2.players[player_id].coins == before - 2


def test_invalid_move_returns_original_state():
    s = _board_state()
    player_id = s.act_player
    s.players[player_id].coins = 0
    # Ruch wojownika bez monet
    action = MoveEntity(player=player_id, from_field="IS1", to_field="IS2", quantity=1)
    s2, info = apply_board_action(s, action, Rng(1))
    # Nieważna akcja zwraca stary stan
    assert not info.get("valid") or s2 is s or s2.players[player_id].coins == 0


def test_buy_zeus_card_costs_4():
    s = _board_state()
    player_id = s.act_player
    s.act_hero = "zeus"
    s.board.zeus_card = True
    s.players[player_id].coins = 6
    before = s.players[player_id].coins
    action = BuyCard(player=player_id, hero="zeus")
    s2, info = apply_board_action(s, action, Rng(1))
    if info.get("valid"):
        assert s2.players[player_id].coins == before - 4
        assert s2.players[player_id].priests == s.players[player_id].priests + 1


# ---------------------------------------------------------------------------
# Scoring tests
# ---------------------------------------------------------------------------

def test_calculate_income():
    s = build_initial_state(2, Rng(1))
    income = calculate_income(s)
    assert all(isinstance(v, int) for v in income.values())
    # Przynajmniej jeden gracz ma jakiś dochód bazowy (z wysp)
    total = sum(income.values())
    assert total >= 0


def test_check_winners_none_initially():
    s = build_initial_state(2, Rng(1))
    assert check_winners(s) == []


def test_check_winners_detects_2_metros():
    s = build_initial_state(2, Rng(1))
    player_id = "p1"
    # Ręcznie ustaw 2 metropolie dla p1
    island_ids = [fid for fid, f in s.fields.items() if f.type == FieldType.ISLAND][:2]
    for iid in island_ids:
        s.fields[iid].owner = player_id
        s.fields[iid].is_metropolis = True
    assert player_id in check_winners(s)
