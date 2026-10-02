"""Niezmienniki stanu po każdym kroku losowych partii (port web/e2e/fuzz_api.py)."""
from collections import Counter

import pytest

from engine.agents import RandomAgent
from engine.engine import GameEngine
from engine.rng import Rng
from engine.rules.creatures import CREATURES
from engine.state import FieldType, GameOptions


def _check(s):
    for pid, p in s.players.items():
        assert p.coins >= 0 and p.philosophers >= 0 and p.priests >= 0, pid
    units = Counter()
    for fid, f in s.fields.items():
        q = f.entity.quantity
        assert q >= 0, fid
        if f.type == FieldType.WATER:
            assert (q > 0) == (f.owner is not None), fid
            assert q == 0 or f.entity.kind == "ship", fid
        else:
            assert q == 0 or (f.entity.kind == "warrior" and f.owner), fid
        if q:
            units[(f.owner, f.type)] += q
    assert all(n <= 8 for n in units.values()), units
    kr = s.cards.figures.get("kraken")
    assert not kr or s.fields[kr["field"]].entity.quantity == 0
    if s.options.creatures:
        c, pend = s.cards, s.board.pending or {}
        held = [x for x in c.track if x] + c.deck + c.discard + [
            n for n, f in c.figures.items() if n != "kraken" and f.get("held", True)]
        if pend.get("card") and not pend.get("via_chimera") and pend["card"] not in held:
            held.append(pend["card"])
        assert sorted(held) == sorted(CREATURES), (s.round_no, pend)


@pytest.mark.parametrize("n,dice", [(2, False), (3, True), (4, False), (5, True)])
def test_invariants_hold_through_random_games(n, dice):
    for seed in range(3):
        eng = GameEngine(rng=Rng(seed), options=GameOptions(combat_dice=dice))
        s = eng.new_game(n, Rng(seed))
        agents = {p: RandomAgent(Rng(seed * 11 + i)) for i, p in enumerate(s.players)}
        while not eng.is_terminal(s):
            s, info = eng.step(s, agents[s.act_player].choose({}, eng.legal_actions(s)))
            assert info.get("valid", True), info
            _check(s)
        target = s.options.metros_to_win
        metros = Counter(f.owner for f in s.fields.values() if f.is_metropolis)
        assert s.winners and all(metros[w] >= target for w in s.winners)
