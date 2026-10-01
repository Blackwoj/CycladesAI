"""Zgodność z instrukcją Cyclades (rebel.pl) — każdy test cytuje zasadę."""
import pytest

from engine.actions import ApollonBid, BuyCreature, EndTurn, MoveEntity, PlaceEntity, RollBid
from engine.engine import GameEngine
from engine.rng import Rng
from engine.rules.board import apply_board_action, legal_board_actions, start_player_turn
from engine.rules.combat import resolve_battle
from engine.rules.roll import apply_roll_bid, legal_roll_actions, setup_roll_phase
from engine.rules.setup import build_initial_state
from engine.rules.units import fleet_chain_targets, fleet_destinations
from engine.state import Building, Entity, FieldType, GameOptions, Stage


def _units(s, pid):
    isl = [f for f in s.fields.values() if f.owner == pid and f.type == FieldType.ISLAND]
    wat = [f for f in s.fields.values() if f.owner == pid and f.type == FieldType.WATER]
    return len(isl), sum(f.entity.quantity for f in isl), sum(f.entity.quantity for f in wat)


def _board(n=3, hero="ares", coins=20, options=None):
    s = build_initial_state(n, Rng(1), options)
    s = setup_roll_phase(s, Rng(1))
    s.stage = Stage.BOARD
    s.play_order, s.play_heroes = ["p1"], [hero]
    s = start_player_turn(s)
    s.players["p1"].coins = coins
    return s


# ---- przygotowanie gry ------------------------------------------------------

def test_every_player_starts_with_5_gold_2_islands_2_troops_2_fleets():
    """„Każdy z graczy otrzymuje 5 GP”; ilustracje str. 7–8: 2 wyspy, 2 Oddziały, 2 Floty."""
    s = build_initial_state(5, Rng(1))
    for pid, p in s.players.items():
        assert (p.coins, p.philosophers, p.priests) == (5, 0, 0)
        assert _units(s, pid) == (2, 2, 2), pid


def test_income_is_collected_at_start_of_first_cycle():
    """Cykl: najpierw dochód, potem ofiary — także w cyklu 1 (start: 2 GP dochodu)."""
    s = GameEngine(rng=Rng(1)).new_game(5, Rng(1))
    assert s.stage == Stage.ROLL
    assert {p.coins for p in s.players.values()} == {7}


# ---- licytacja --------------------------------------------------------------

def test_two_player_game_uses_three_gods_two_markers_and_three_metropolises():
    """Str. 6: 2 graczy gra wg zasad dla 4 osób, po 2 ofiary, wygrana = 3 Metropolie."""
    s = GameEngine(rng=Rng(1)).new_game(2, Rng(1))
    assert sum(1 for r, h in s.roll.heros_per_row.items() if h and r != "row_5") == 3
    markers = [s.act_player] + s.roll.bid_order
    assert sorted(markers) == ["p1", "p1", "p2", "p2"]
    assert s.options.metros_to_win == 3


def test_two_player_game_gives_each_player_two_turns():
    eng, rng = GameEngine(rng=Rng(3)), Rng(3)
    s = eng.new_game(2, rng)
    while s.stage == Stage.ROLL:
        s, _ = eng.step(s, legal_roll_actions(s)[0])
    turns = [s.act_player] + s.play_order
    assert sorted(turns) == ["p1", "p1", "p2", "p2"]
    for pid in ("p1", "p2"):
        assert len(set(s.round_heroes[pid])) == 2


def test_outbid_player_must_bid_on_a_different_god():
    """„Gracz przelicytowany … musi natychmiast zalicytować złoto o łaskę u INNEGO boga.”"""
    s = setup_roll_phase(build_initial_state(3, Rng(1)), Rng(1))
    first = s.act_player
    s = apply_roll_bid(s, RollBid(player=first, row="row_1", amount=1))
    second = s.act_player
    s = apply_roll_bid(s, RollBid(player=second, row="row_1", amount=2))
    assert s.act_player == first
    assert not [a for a in legal_roll_actions(s) if isinstance(a, RollBid) and a.row == "row_1"]


def test_offerings_must_be_affordable_in_total():
    """„Nie wolno składać ofiary wyższej od tej, na którą stać gracza.”

    2 graczy: po ofierze 2 z 3 GP drugi znacznik może zaoferować już tylko 1.
    """
    s = setup_roll_phase(build_initial_state(2, Rng(1)), Rng(1))
    pid = s.act_player
    s.players[pid].coins = 3
    s = apply_roll_bid(s, RollBid(player=pid, row="row_1", amount=2))
    s.act_player = pid                    # drugi znacznik tego samego gracza
    bids = [a.amount for a in legal_roll_actions(s) if isinstance(a, RollBid) and a.row != "row_1"]
    assert bids and max(bids) == 1


def test_next_cycle_bidding_order_is_reverse_of_action_order():
    """Kto skończył akcje ostatni, ten pierwszy składa ofiarę w następnym cyklu."""
    s = build_initial_state(3, Rng(1))
    s.acted = ["p2", "p3", "p1"]
    s = setup_roll_phase(s, Rng(1))
    assert [s.act_player] + s.roll.bid_order == ["p1", "p3", "p2"]


# ---- rekrutacja i ruch ------------------------------------------------------

def test_recruit_at_most_four_per_turn():
    """„Gracz nie może zakupić więcej niż 3 dodatkowe Oddziały w jednej turze.”"""
    s = _board(hero="ares", coins=50)
    for _ in range(4):
        rec = next(a for a in legal_board_actions(s) if isinstance(a, PlaceEntity))
        s, info = apply_board_action(s, rec, Rng(1))
        assert info["valid"]
    assert not [a for a in legal_board_actions(s) if isinstance(a, PlaceEntity)]
    assert s.players["p1"].coins == 50 - (0 + 2 + 3 + 4)


def test_max_eight_troops_on_board():
    s = _board(hero="ares", coins=50)
    isl = sorted(fid for fid, f in s.fields.items() if f.owner == "p1" and f.type == FieldType.ISLAND)[0]
    s.fields[isl].entity.quantity = 7     # + 1 na drugiej wyspie = 8
    assert not [a for a in legal_board_actions(s) if isinstance(a, PlaceEntity)]


def test_fleet_moves_up_to_three_fields_for_one_gold():
    """Posejdon: „Za 1 GP … Floty z jednego pola na odległość maksymalnie 3 pól.”"""
    s = _board(hero="posejdon")
    src = next(fid for fid, f in s.fields.items() if f.owner == "p1" and f.type == FieldType.WATER)
    one = set(fleet_destinations(s, src, "p1", max_steps=1))
    three = set(fleet_destinations(s, src, "p1"))
    assert one < three
    dst = sorted(three - one)[0]
    s2, info = apply_board_action(s, MoveEntity(player="p1", from_field=src, to_field=dst, quantity=1), Rng(1))
    assert info["valid"] and s2.players["p1"].coins == 19


def test_troops_travel_only_along_own_fleet_chain():
    """Ares: wyspa docelowa połączona z wyjściową „łańcuchem Flot swojego koloru”."""
    s = _board(hero="ares")
    src = sorted(fid for fid, f in s.fields.items() if f.owner == "p1" and f.type == FieldType.ISLAND)[0]
    for f in s.fields.values():                       # bez flot — brak ruchu
        if f.type == FieldType.WATER and f.owner == "p1":
            f.owner, f.entity = None, Entity()
    assert fleet_chain_targets(s, src, "p1") == []
    water = next(nb for nb in s.fields[src].neighbors if s.fields[nb].type == FieldType.WATER)
    s.fields[water].owner, s.fields[water].entity = "p1", Entity("ship", 1)
    reach = fleet_chain_targets(s, src, "p1")
    assert reach and all(water in s.fields[i].neighbors for i in reach)


def test_cannot_attack_last_island_unless_it_wins():
    """„Gracz NIE może zaatakować ostatniej wyspy innego gracza, chyba że … wygrałby.”"""
    from engine.rules.units import may_attack_island
    s = _board(n=3)
    p2_islands = sorted(fid for fid, f in s.fields.items() if f.owner == "p2" and f.type == FieldType.ISLAND)
    s.fields[p2_islands[1]].owner = None
    last = p2_islands[0]
    assert not may_attack_island(s, "p1", last)
    s.fields[last].is_metropolis = True
    mine = sorted(fid for fid, f in s.fields.items() if f.owner == "p1" and f.type == FieldType.ISLAND)
    s.fields[mine[0]].is_metropolis = True            # 1 + zdobyta = 2 = wygrana
    assert may_attack_island(s, "p1", last)


def test_empty_enemy_island_is_captured_without_battle():
    from engine.rules.units import land_troops_into
    s = _board(n=3)
    src = next(fid for fid, f in s.fields.items() if f.owner == "p1" and f.type == FieldType.ISLAND)
    tgt = next(fid for fid, f in s.fields.items() if f.owner == "p2" and f.type == FieldType.ISLAND)
    s.fields[tgt].entity = Entity()
    info = land_troops_into(s, "p1", src, tgt, 1, Rng(1))
    assert not info["combat"] and s.fields[tgt].owner == "p1"


# ---- bitwy ------------------------------------------------------------------

def _battle_state(dice=False, defenders=2, forts=0):
    s = _board(n=3, options=GameOptions(combat_dice=dice))
    tgt = next(fid for fid, f in s.fields.items() if f.owner == "p2" and f.type == FieldType.ISLAND)
    s.fields[tgt].entity = Entity("warrior", defenders)
    slots = list(s.fields[tgt].buildings)
    for sl in slots[:forts]:
        s.fields[tgt].buildings[sl] = Building("ares")
    return s, tgt


def test_battle_loser_of_each_round_loses_one_unit_tie_both():
    s, tgt = _battle_state(defenders=2)
    info = resolve_battle(s, tgt, "p1", 3, Rng(1))
    # bez kości: 3v2 → obrońca traci; 3v1 → traci; atakujący zostaje z 3
    assert info["winner"] == "p1" and s.fields[tgt].entity.quantity == 3
    s, tgt = _battle_state(defenders=2)
    info = resolve_battle(s, tgt, "p1", 2, Rng(1))
    # remisy: obie strony tracą po 1 aż do zera — wyspa zostaje obrońcy
    assert info["winner"] == "p2" and s.fields[tgt].owner == "p2" and s.fields[tgt].entity.quantity == 0


def test_fortress_adds_one_to_defence():
    # 3 v 2+1: remis, remis → atakujący wygrywa, ale zostaje mu 1 Oddział (bez Fortecy: 3)
    s, tgt = _battle_state(defenders=2, forts=1)
    info = resolve_battle(s, tgt, "p1", 3, Rng(1))
    assert info["winner"] == "p1" and s.fields[tgt].entity.quantity == 1
    # 2 v 2+1: obrońca wygrywa każdą rundę
    s, tgt = _battle_state(defenders=2, forts=1)
    assert resolve_battle(s, tgt, "p1", 2, Rng(1))["winner"] == "p2"
    assert s.fields[tgt].entity.quantity == 2


def test_combat_dice_option_makes_battles_random():
    outcomes = set()
    for seed in range(40):
        s, tgt = _battle_state(dice=True, defenders=2)
        outcomes.add(resolve_battle(s, tgt, "p1", 2, Rng(seed))["winner"])
    assert outcomes == {"p1", "p2"}


# ---- koniec gry -------------------------------------------------------------

@pytest.mark.parametrize("dice", [False, True])
def test_full_random_games_finish_without_rejected_actions(dice):
    from engine.agents import RandomAgent
    for n in (2, 4):
        eng = GameEngine(rng=Rng(n), options=GameOptions(combat_dice=dice))
        s = eng.new_game(n, Rng(n))
        agents = {p: RandomAgent(Rng(i)) for i, p in enumerate(s.players)}
        for _ in range(3000):
            if eng.is_terminal(s):
                break
            legal = eng.legal_actions(s)
            assert legal
            s, info = eng.step(s, agents[s.act_player].choose({}, legal))
            assert info.get("valid", True), info
        assert eng.is_terminal(s) and eng.winner(s)
