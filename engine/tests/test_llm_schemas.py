"""Testy schematów Pydantic dla wyjścia LLM."""
import pytest

pytest.importorskip("pydantic", reason="pydantic>=2.0 required")

from engine.agents.llm_schemas import (
    action_from_llm_output,
    guided_choice_from_llm_output,
    json_schema_for_hero,
    GuidedChoiceSchema,
)
from engine.actions import PlaceEntity, MoveEntity, Build, BuyCard, EndTurn, RollBid, ApollonBid


# ---- json_schema_for_hero ------------------------------------------------

def test_schema_ares_is_dict():
    s = json_schema_for_hero("ares", "board")
    assert isinstance(s, dict)


def test_schema_roll_phase():
    s = json_schema_for_hero("", "roll")
    assert isinstance(s, dict)


# ---- action_from_llm_output — poprawne akcje ----------------------------

def test_parse_end_turn():
    a = action_from_llm_output({"action_type": "end_turn"}, "p1", "apollon", "board")
    assert isinstance(a, EndTurn)
    assert a.player == "p1"


def test_parse_place_warrior_ares():
    a = action_from_llm_output(
        {"action_type": "place_entity", "field_id": "island_1", "quantity": 1},
        "p1", "ares", "board"
    )
    assert isinstance(a, PlaceEntity)
    assert a.kind == "warrior"
    assert a.field_id == "island_1"


def test_parse_place_ship_posejdon():
    a = action_from_llm_output(
        {"action_type": "place_entity", "field_id": "water_1", "quantity": 2},
        "p1", "posejdon", "board"
    )
    assert isinstance(a, PlaceEntity)
    assert a.kind == "ship"


def test_parse_buy_philosopher_atena():
    a = action_from_llm_output(
        {"action_type": "buy_card", "hero": "atena"},
        "p1", "atena", "board"
    )
    assert isinstance(a, BuyCard)
    assert a.hero == "atena"


def test_parse_buy_priest_zeus():
    a = action_from_llm_output(
        {"action_type": "buy_card", "hero": "zeus"},
        "p1", "zeus", "board"
    )
    assert isinstance(a, BuyCard)
    assert a.hero == "zeus"


def test_parse_roll_bid():
    a = action_from_llm_output(
        {"action_type": "roll_bid", "row": "row_2", "amount": 3},
        "p1", "", "roll"
    )
    assert isinstance(a, RollBid)
    assert a.row == "row_2"
    assert a.amount == 3


def test_parse_apollon_bid():
    a = action_from_llm_output(
        {"action_type": "apollon_bid"},
        "p1", "", "roll"
    )
    assert isinstance(a, ApollonBid)


# ---- action_from_llm_output — niepoprawne / nieegzystujące akcje --------

def test_wrong_hero_returns_none():
    """Zeus nie może PlaceEntity."""
    a = action_from_llm_output(
        {"action_type": "place_entity", "field_id": "x", "quantity": 1},
        "p1", "zeus", "board"
    )
    assert a is None


def test_invalid_action_type_returns_none():
    a = action_from_llm_output({"action_type": "fly_to_moon"}, "p1", "ares", "board")
    assert a is None


def test_missing_required_field_returns_none():
    """move_entity bez from_field → None."""
    a = action_from_llm_output(
        {"action_type": "move_entity", "to_field": "x", "quantity": 1},
        "p1", "ares", "board"
    )
    assert a is None


# ---- guided_choice_from_llm_output ---------------------------------------

def test_guided_valid_index():
    assert guided_choice_from_llm_output({"action_index": 2}, 5) == 2


def test_guided_out_of_range_returns_zero():
    assert guided_choice_from_llm_output({"action_index": 10}, 5) == 0


def test_guided_negative_returns_zero():
    assert guided_choice_from_llm_output({"action_index": -1}, 5) == 0


def test_guided_missing_field_returns_zero():
    assert guided_choice_from_llm_output({}, 5) == 0
