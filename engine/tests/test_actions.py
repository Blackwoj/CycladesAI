"""Testy typów akcji — serializacja round-trip i kontrakt agenta."""
import pytest

from engine.actions import (
    Build,
    EndTurn,
    PlaceEntity,
    PlayCard,
    RollBid,
    action_from_dict,
)
from engine.agents import RandomAgent
from engine.rng import Rng


@pytest.mark.parametrize("action", [
    RollBid(player="p1", row="row_1", amount=4),
    PlaceEntity(player="p2", field_id="f3", kind="warrior", quantity=2),
    Build(player="p1", field_id="f3", hero="ares"),
    PlayCard(player="p1", card_id="c_kraken", targets=("f3", "f4")),
    EndTurn(player="p2"),
])
def test_action_roundtrip(action):
    restored = action_from_dict(action.to_dict())
    assert restored == action


def test_random_agent_picks_from_legal():
    actions = [RollBid(player="p1", row=f"row_{i}", amount=i) for i in range(1, 5)]
    agent = RandomAgent(Rng(123))
    chosen = agent.choose(state_view={}, legal_actions=actions)
    assert chosen in actions


def test_random_agent_is_deterministic_with_seed():
    actions = [RollBid(player="p1", row=f"row_{i}", amount=i) for i in range(1, 5)]
    a = RandomAgent(Rng(7)).choose({}, actions)
    b = RandomAgent(Rng(7)).choose({}, actions)
    assert a == b


def test_random_agent_raises_on_empty():
    with pytest.raises(ValueError):
        RandomAgent(Rng(1)).choose({}, [])
