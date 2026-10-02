"""Mitologiczne Stwory — tor, koszty, efekty (książeczka „Potwory”)."""
import pytest

from engine.actions import BuyCreature, EndTurn, MoveEntity, PlayCard, ReplaceCreature
from engine.engine import GameEngine
from engine.rng import Rng
from engine.rules.board import apply_board_action, legal_board_actions, start_player_turn
from engine.rules.creatures import CREATURES, creature_cost, pending_actions, update_track
from engine.rules.roll import setup_roll_phase
from engine.rules.setup import build_initial_state
from engine.state import Building, Entity, FieldType, Stage

DONE = ("done",)


def _turn(hero="ares", coins=20, card=None):
    s = build_initial_state(3, Rng(1))
    s = setup_roll_phase(s, Rng(1))
    s.stage = Stage.BOARD
    s.play_order, s.play_heroes = ["p1"], [hero]
    s = start_player_turn(s)
    s.players["p1"].coins = coins
    if card:
        s.cards.track = [card, None, None]
        if card in s.cards.deck:
            s.cards.deck.remove(card)
    return s


def _buy(s, slot=0):
    s, info = apply_board_action(s, BuyCreature(player="p1", slot=slot), Rng(1))
    assert info["valid"], info
    return s


def _play(s, card, *targets):
    s, info = apply_board_action(s, PlayCard(player="p1", card_id=card, targets=tuple(targets)), Rng(1))
    assert info["valid"], info
    return s, info


def _isl(s, pid):
    return sorted(fid for fid, f in s.fields.items() if f.owner == pid and f.type == FieldType.ISLAND)


def _sea(s, pid):
    return sorted(fid for fid, f in s.fields.items() if f.owner == pid and f.type == FieldType.WATER)


# ---- tor --------------------------------------------------------------------

def test_deck_has_17_unique_creatures():
    s = build_initial_state(3, Rng(1))
    assert sorted(s.cards.deck) == sorted(CREATURES) and len(CREATURES) == 17


def test_track_fills_one_two_then_three_slots():
    """Cykl 1: tylko pole 4 GP; cykl 2: 4 i 3 GP; potem wszystkie 3."""
    s = build_initial_state(3, Rng(1))
    s.round_no = 1
    update_track(s, Rng(1))
    assert s.cards.track[0] and s.cards.track[1:] == [None, None]
    first = s.cards.track[0]
    s.round_no = 2
    update_track(s, Rng(1))
    assert s.cards.track[1] == first and s.cards.track[0] and s.cards.track[2] is None
    s.round_no = 3
    update_track(s, Rng(1))
    assert s.cards.track[2] == first and all(s.cards.track)
    s.round_no = 4
    update_track(s, Rng(1))
    assert first in s.cards.discard               # nieużyty z pola 2 GP odpada


def test_creature_cost_and_temple_discount_once_per_cycle():
    s = _turn(card="harpia")
    assert creature_cost(s, "p1", 0) == (4, 0)
    isl = _isl(s, "p1")[0]
    s.fields[isl].buildings[next(iter(s.fields[isl].buildings))] = Building("zeus")
    assert creature_cost(s, "p1", 0) == (3, 1)
    s = _buy(s)
    assert s.players["p1"].coins == 17
    assert creature_cost(s, "p1", 0) == (4, 0)    # zniżka zużyta w tym cyklu


def test_apollo_cannot_summon_creatures():
    s = _turn(hero="apollon", card="harpia")
    assert not [a for a in legal_board_actions(s) if isinstance(a, BuyCreature)]


def test_zeus_replaces_creature_for_one_gold():
    s = _turn(hero="zeus", card="harpia")
    s, info = apply_board_action(s, ReplaceCreature(player="p1", slot=0), Rng(1))
    assert info["valid"] and s.cards.track[0] != "harpia" and "harpia" in s.cards.discard
    assert s.players["p1"].coins == 19


def test_pending_creature_blocks_other_actions_and_done_finishes():
    s = _buy(_turn(card="harpia"))
    assert all(isinstance(a, PlayCard) for a in legal_board_actions(s))
    _, info = apply_board_action(s, EndTurn(player="p1"), Rng(1))
    assert not info["valid"]
    s, _ = _play(s, "harpia", *DONE)
    assert s.board.pending is None


# ---- efekty -----------------------------------------------------------------

def test_harpia_removes_enemy_troop():
    s = _buy(_turn(card="harpia"))
    tgt = _isl(s, "p2")[0]
    s, _ = _play(s, "harpia", tgt)
    assert s.fields[tgt].entity.quantity == 0 and s.fields[tgt].owner == "p2"


def test_pegaz_flies_troops_without_fleets():
    s = _turn(card="pegaz")
    for fid in _sea(s, "p1"):
        s.fields[fid].owner, s.fields[fid].entity = None, Entity()
    s = _buy(s)
    src = _isl(s, "p1")[0]
    dst = next(fid for fid, f in s.fields.items() if f.type == FieldType.ISLAND and f.owner is None)
    s, _ = _play(s, "pegaz", src, dst, 1)
    assert s.fields[dst].owner == "p1" and s.fields[dst].entity.quantity == 1


def test_gigant_destroys_building_but_not_metropolis():
    s = _turn(card="gigant")
    tgt = _isl(s, "p2")[0]
    slot = next(iter(s.fields[tgt].buildings))
    s.fields[tgt].buildings[slot] = Building("ares")
    met = _isl(s, "p2")[1]
    s.fields[met].is_metropolis = True
    s.fields[met].buildings[next(iter(s.fields[met].buildings))] = Building("zeus")
    s = _buy(s)
    assert all(a.targets[0] != met for a in pending_actions(s) if a.targets != DONE)
    s, _ = _play(s, "gigant", tgt, slot)
    assert s.fields[tgt].buildings[slot] is None


def test_chiron_protects_against_harpia():
    s = _turn(card="chiron")
    tgt = _isl(s, "p2")[0]
    s = _buy(s)
    s, _ = _play(s, "chiron", tgt)
    s.cards.track[0] = "harpia"
    s = _buy(s)
    assert all(a.targets == DONE or a.targets[0] != tgt for a in pending_actions(s))


def test_gryf_steals_half_gold_rounded_down():
    s = _buy(_turn(card="gryf"))
    s.players["p2"].coins = 7
    s, info = _play(s, "gryf", "p2")
    assert s.players["p2"].coins == 4 and info["loot"] == 3


def test_satyr_and_driada_steal_cards():
    s = _turn(card="satyr")
    s.players["p2"].philosophers = 1
    s, _ = _play(_buy(s), "satyr", "p2")
    assert (s.players["p1"].philosophers, s.players["p2"].philosophers) == (1, 0)
    s = _turn(card="driada")
    s.players["p2"].priests = 2
    s, _ = _play(_buy(s), "driada", "p2")
    assert (s.players["p1"].priests, s.players["p2"].priests) == (1, 1)


def test_satyr_fourth_philosopher_forces_metropolis():
    s = _turn(card="satyr")
    s.players["p1"].philosophers = 3
    s.players["p2"].philosophers = 1
    s, _ = _play(_buy(s), "satyr", "p2")
    assert s.board.pending == {"kind": "metropolis", "source": "philosophers"}


def test_mojry_pays_income_again():
    s = _turn(card="mojry")
    from engine.rules.scoring import calculate_income
    expected = 20 - 4 + calculate_income(s)["p1"]
    s = _buy(s)
    assert s.players["p1"].coins == expected and s.board.pending is None


def test_sfinks_sells_units_and_cards_for_two_each():
    s = _turn(card="sfinks")
    s.players["p1"].priests = 1
    s = _buy(s)
    s, _ = _play(s, "sfinks", "priest")
    s, _ = _play(s, "sfinks", "ship", _sea(s, "p1")[0])
    s, _ = _play(s, "sfinks", *DONE)
    assert s.players["p1"].coins == 16 + 4 and s.players["p1"].priests == 0


def test_cyklopi_swap_completing_set_forces_metropolis():
    s = _turn(card="cyklopi")
    slots = [(fid, sl) for fid in _isl(s, "p1") for sl in s.fields[fid].buildings]
    for (fid, sl), h in zip(slots, ["ares", "posejdon", "atena", "atena"]):
        s.fields[fid].buildings[sl] = Building(h)
    s = _buy(s)
    fid, sl = slots[3]
    s, _ = _play(s, "cyklopi", fid, sl, "zeus")
    assert s.board.pending == {"kind": "metropolis", "source": "buildings"}


def test_syrena_replaces_isolated_enemy_fleet():
    s = _buy(_turn(card="syrena"))
    tgt = next(a.targets[0] for a in pending_actions(s) if a.targets != DONE)
    s, _ = _play(s, "syrena", tgt)
    assert s.fields[tgt].owner == "p1" and s.fields[tgt].entity.quantity == 1


def test_sylfida_moves_fleets_ten_steps_without_poseidon():
    s = _buy(_turn(hero="zeus", card="sylfida"))
    for _ in range(10):
        a = next(a for a in pending_actions(s) if a.targets != DONE)
        s, _ = apply_board_action(s, a, Rng(1))
    assert [a.targets for a in pending_actions(s)] == [DONE]


def test_kraken_destroys_fleets_and_blocks_field():
    s = _buy(_turn(card="kraken"))
    tgt = _sea(s, "p2")[0]
    s, _ = _play(s, "kraken", tgt)
    assert s.fields[tgt].entity.quantity == 0 and s.fields[tgt].owner is None
    s, _ = _play(s, "kraken", *DONE)
    from engine.rules.units import water_blocked
    assert water_blocked(s, tgt)


def test_meduza_freezes_troops_and_expires_on_owners_next_turn():
    s = _turn(card="meduza")
    src = _isl(s, "p1")[0]
    s, _ = _play(_buy(s), "meduza", src)
    assert not [a for a in legal_board_actions(s) if isinstance(a, MoveEntity) and a.from_field == src]
    s2 = start_player_turn(s.__class__.from_dict({**s.to_dict(), "play_order": ["p1"], "play_heroes": ["ares"]}))
    assert "meduza" not in s2.cards.figures and "meduza" in s2.cards.discard


def test_minotaur_defends_with_strength_two():
    from engine.rules.combat import resolve_battle
    s = _turn(card="minotaur")
    tgt = _isl(s, "p2")[0]
    s, _ = _play(_buy(s), "minotaur", tgt)
    s.fields[tgt].entity = Entity("warrior", 1)
    no_mino = s.__class__.from_dict(s.to_dict())
    no_mino.cards.figures.pop("minotaur")
    assert resolve_battle(no_mino, tgt, "p1", 2, Rng(1))["winner"] == "p1"
    info = resolve_battle(s, tgt, "p1", 2, Rng(1))        # 2 v 1+2
    assert info["winner"] == "p2" and s.fields[tgt].entity.quantity == 1


def test_two_figures_on_one_island_destroy_each_other():
    s = _turn(card="chiron")
    isl = _isl(s, "p1")[0]
    s, _ = _play(_buy(s), "chiron", isl)
    s.cards.track[0] = "meduza"
    s, _ = _play(_buy(s), "meduza", isl)
    assert not s.cards.figures and {"chiron", "meduza"} <= set(s.cards.discard)


def test_polifem_pushes_adjacent_fleets():
    s = _turn(card="polifem")
    isl = _isl(s, "p1")[0]
    ring = [nb for nb in s.fields[isl].neighbors if s.fields[nb].type == FieldType.WATER]
    s.fields[ring[0]].owner, s.fields[ring[0]].entity = "p2", Entity("ship", 1)
    s, _ = _play(_buy(s), "polifem", isl)
    assert all(s.fields[r].entity.quantity == 0 for r in ring)


def test_chimera_uses_power_of_discarded_creature_and_reshuffles():
    s = _turn(card="chimera")
    s.cards.discard = ["gryf"]
    s = _buy(s)
    s, info = _play(s, "chimera", "gryf")
    assert s.board.pending["card"] == "gryf" and s.cards.discard == []
    assert "chimera" in s.cards.deck and "gryf" in s.cards.deck


def test_games_with_creatures_use_them_and_finish():
    from collections import Counter
    from engine.agents import RandomAgent
    used = Counter()
    for seed in range(4):
        eng = GameEngine(rng=Rng(seed))
        s = eng.new_game(3, Rng(seed))
        agents = {p: RandomAgent(Rng(seed * 7 + i)) for i, p in enumerate(s.players)}
        while not eng.is_terminal(s):
            a = agents[s.act_player].choose({}, eng.legal_actions(s))
            if a.type == "play_card":
                used[a.card_id] += 1
            s, info = eng.step(s, a)
            assert info.get("valid", True), info
    assert len(used) >= 10


# ---- księgowość kart figurek (błędy znalezione fuzzem API) -------------------

def _all_cards(s):
    c = s.cards
    held = [n for n, f in c.figures.items() if n != "kraken" and f.get("held", True)]
    return sorted([x for x in c.track if x] + c.deck + c.discard + held)


def test_figure_card_returns_when_effect_is_skipped():
    s = _buy(_turn(card="meduza"))
    s, _ = _play(s, "meduza", *DONE)
    assert "meduza" in s.cards.discard and _all_cards(s) == sorted(CREATURES)


def test_relocating_figure_does_not_duplicate_its_card():
    from engine.rules.creatures import _place_figure
    s = _turn()
    a, b = _isl(s, "p1")
    s.cards.deck.remove("meduza")
    s.cards.figures["meduza"] = {"field": a, "owner": "p2", "held": True}
    _place_figure(s, "p1", "meduza", b, held=False)       # np. przez Chimerę
    assert s.cards.figures["meduza"] == {"field": b, "owner": "p1", "held": True}
    assert _all_cards(s) == sorted(CREATURES)


def test_chimera_copying_moirai_resolves_once():
    s = _turn(card="chimera")
    s.cards.deck.remove("mojry"); s.cards.discard = ["mojry"]
    s, _ = _play(_buy(s), "chimera", "mojry")
    assert s.board.pending is None and _all_cards(s) == sorted(CREATURES)


def test_figure_placed_via_chimera_holds_no_card():
    s = _turn(card="chimera")
    s.cards.deck.remove("minotaur"); s.cards.discard = ["minotaur"]
    s = _buy(s)
    s, _ = _play(s, "chimera", "minotaur")
    s, _ = _play(s, "minotaur", _isl(s, "p1")[0])
    assert s.cards.figures["minotaur"]["held"] is False
    assert _all_cards(s) == sorted(CREATURES)
    from engine.rules.creatures import expire_figures
    expire_figures(s, "p1")
    assert _all_cards(s) == sorted(CREATURES)


def test_creature_cards_conserved_in_random_games():
    from engine.agents import RandomAgent
    for seed in range(6):
        eng = GameEngine(rng=Rng(seed))
        s = eng.new_game(3, Rng(seed))
        agents = {p: RandomAgent(Rng(seed * 3 + i)) for i, p in enumerate(s.players)}
        while not eng.is_terminal(s):
            s, _ = eng.step(s, agents[s.act_player].choose({}, eng.legal_actions(s)))
            pend = s.board.pending or {}
            cards = _all_cards(s)
            if pend.get("card") and not pend.get("via_chimera") and pend["card"] not in cards:
                cards = sorted(cards + [pend["card"]])
            assert cards == sorted(CREATURES), (seed, s.round_no, pend)
