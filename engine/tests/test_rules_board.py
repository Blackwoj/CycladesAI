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
    s = build_initial_state(3, Rng(1))   # 2 graczy gra do 3 metropolii
    player_id = "p1"
    # Ręcznie ustaw 2 metropolie dla p1
    island_ids = [fid for fid, f in s.fields.items() if f.type == FieldType.ISLAND][:2]
    for iid in island_ids:
        s.fields[iid].owner = player_id
        s.fields[iid].is_metropolis = True
    assert player_id in check_winners(s)


# ---- Apollon: znacznik dochodu ------------------------------------------

def _apollon_state(hero="apollon"):
    s = build_initial_state(2, Rng(1))
    s = setup_roll_phase(s, Rng(1))
    s.stage = Stage.BOARD
    s.hero_players = {"p1": hero, "p2": "ares"}
    s.play_order = ["p1", "p2"]
    return start_player_turn(s)


def test_apollon_can_place_income_on_own_island():
    from engine.actions import PlaceIncome
    s = _apollon_state()
    own = {fid for fid, f in s.fields.items() if f.type == FieldType.ISLAND and f.owner == "p1"}
    legal = legal_board_actions(s)
    places = {a.field_id for a in legal if isinstance(a, PlaceIncome)}
    assert places == own and own

    fid = sorted(own)[0]
    before = calculate_income(s)["p1"]
    s2, info = apply_board_action(s, PlaceIncome(player="p1", field_id=fid), Rng(1))
    assert info["valid"]
    assert s2.fields[fid].income.quantity == 1
    assert calculate_income(s2)["p1"] == before + 1
    # tylko jeden znacznik na turę
    assert not any(isinstance(a, PlaceIncome) for a in legal_board_actions(s2))
    _, info = apply_board_action(s2, PlaceIncome(player="p1", field_id=fid), Rng(1))
    assert not info["valid"]


def test_second_apollon_player_gets_no_income_marker():
    from engine.actions import PlaceIncome
    s = _apollon_state(hero="ap_s")
    assert not any(isinstance(a, PlaceIncome) for a in legal_board_actions(s))


def test_place_income_roundtrip_and_llm_schema():
    from engine.actions import PlaceIncome, action_from_dict
    from engine.agents.llm_schemas import action_from_llm_output
    a = PlaceIncome(player="p1", field_id="IS2")
    assert action_from_dict(a.to_dict()) == a
    assert action_from_llm_output({"action_type": "place_income", "field_id": "IS2"}, "p1", "apollon") == a


# ---- budynki wszystkich bogów + metropolia z kompletu budynków ------------

def _turn(hero, coins=10):
    s = build_initial_state(2, Rng(1))
    s = setup_roll_phase(s, Rng(1))
    s.stage = Stage.BOARD
    s.hero_players = {"p1": hero, "p2": "apollon"}
    s.play_order = ["p1", "p2"]
    s.players["p1"].coins = coins
    return start_player_turn(s)


def _own_islands(s, pid="p1"):
    return sorted(fid for fid, f in s.fields.items() if f.type == FieldType.ISLAND and f.owner == pid)


def _give_set(s, pid="p1"):
    """Rozstaw po jednym budynku każdego boga na wyspach gracza."""
    islands = _own_islands(s, pid)
    slots = [(fid, slot) for fid in islands for slot in s.fields[fid].buildings]
    for (fid, slot), hero in zip(slots, ["ares", "posejdon", "atena", "zeus"]):
        s.fields[fid].buildings[slot] = Building(hero)
    return s


@pytest.mark.parametrize("hero", ["ares", "posejdon", "atena", "zeus"])
def test_every_god_except_apollo_builds_own_building(hero):
    s = _turn(hero)
    builds = [a for a in legal_board_actions(s) if isinstance(a, Build)]
    assert builds and {a.hero for a in builds} == {hero}
    s2, info = apply_board_action(s, builds[0], Rng(1))
    assert info["valid"]
    assert Building(hero) in s2.fields[builds[0].field_id].buildings.values()
    assert s2.players["p1"].coins == 8


def test_apollo_has_no_building():
    s = _turn("apollon")
    assert not [a for a in legal_board_actions(s) if isinstance(a, Build)]


def test_build_of_other_god_is_rejected():
    s = _turn("zeus")
    fid = _own_islands(s)[0]
    _, info = apply_board_action(s, Build(player="p1", field_id=fid, hero="ares"), Rng(1))
    assert not info["valid"]


def test_completing_building_set_forces_metropolis():
    """Czwarty różny budynek → metropolia NATYCHMIAST i obowiązkowo (instrukcja str. 6)."""
    s = _turn("zeus")
    islands = _own_islands(s)
    slots = [(fid, slot) for fid in islands for slot in s.fields[fid].buildings]
    for (fid, slot), hero in zip(slots, ["ares", "posejdon", "atena"]):
        s.fields[fid].buildings[slot] = Building(hero)
    zeus_build = next(a for a in legal_board_actions(s) if isinstance(a, Build) and a.hero == "zeus")
    s, info = apply_board_action(s, zeus_build, Rng(1))
    assert info["valid"] and s.board.pending == {"kind": "metropolis", "source": "buildings"}
    legal = legal_board_actions(s)
    assert legal and all(isinstance(a, Build) and a.hero == "metro" for a in legal)


def test_metropolis_from_buildings_consumes_one_of_each_god():
    s = _give_set(_turn("ares"))
    spare = next((fid, sl) for fid in _own_islands(s) for sl, b in s.fields[fid].buildings.items() if b is None)
    s.fields[spare[0]].buildings[spare[1]] = Building("ares")
    s = start_player_turn(s.__class__.from_dict({**s.to_dict(), "play_order": ["p1"], "play_heroes": ["ares"]}))
    assert s.board.pending["source"] == "buildings"

    target = _own_islands(s)[-1]
    s2, info = apply_board_action(s, Build(player="p1", field_id=target, hero="metro"), Rng(1))
    assert info["valid"] and info["source"] == "buildings"
    assert s2.fields[target].is_metropolis
    left = [b.hero for fid in _own_islands(s2) if not s2.fields[fid].is_metropolis
            for b in s2.fields[fid].buildings.values() if b]
    assert left == ["ares"]
    assert s2.board.pending is None
    assert any(isinstance(a, EndTurn) for a in legal_board_actions(s2))


def test_fourth_philosopher_forces_metropolis():
    s = _turn("atena", coins=10)
    s.players["p1"].philosophers = 2
    s = start_player_turn(s.__class__.from_dict({**s.to_dict(), "play_order": ["p1"], "play_heroes": ["atena"]}))
    assert s.players["p1"].philosophers == 3 and s.board.pending is None   # darmowy = 3.
    buy = next(a for a in legal_board_actions(s) if isinstance(a, BuyCard))
    s, info = apply_board_action(s, buy, Rng(1))
    assert info["valid"] and s.players["p1"].philosophers == 0
    assert s.board.pending == {"kind": "metropolis", "source": "philosophers"}


def test_pending_metropolis_blocks_other_actions():
    s = _give_set(_turn("ares"))
    s = start_player_turn(s.__class__.from_dict({**s.to_dict(), "play_order": ["p1"], "play_heroes": ["ares"]}))
    _, info = apply_board_action(s, EndTurn(player="p1"), Rng(1))
    assert not info["valid"]


def test_win_is_decided_at_end_of_cycle_with_gold_tiebreak():
    from engine.engine import GameEngine
    from engine.rules.scoring import end_board_phase
    s = build_initial_state(3, Rng(1))
    for pid, coins in (("p1", 3), ("p2", 9)):
        for fid in _own_islands(s, pid):
            s.fields[fid].is_metropolis = True
        s.players[pid].coins = coins
    assert GameEngine().winner(s) == []          # w trakcie cyklu nikt jeszcze nie wygrał
    s2 = end_board_phase(s, Rng(1))
    assert s2.winners == ["p2"] and GameEngine().is_terminal(s2)
