"""Testy warstwy stanu (Faza 1) — to są realne gwarancje, nie zaślepki.

Sprawdzamy dwie własności krytyczne dla MCTS i eksperymentów:
1. clone() daje w pełni niezależną kopię,
2. to_dict()/from_dict() to wierny round-trip.
"""
from engine.state import (
    Building,
    Entity,
    Field,
    FieldType,
    GameState,
    Income,
    Player,
    Stage,
)


def _sample_state() -> GameState:
    state = GameState(
        num_of_players=2,
        stage=Stage.BOARD,
        round_no=3,
        act_player="p1",
        act_hero="ares",
        play_order=["p1", "p2"],
        hero_players={"p1": "ares", "p2": "atena"},
        players={
            "p1": Player("p1", coins=7, philosophers=1, priests=2),
            "p2": Player("p2", coins=3),
        },
        fields={
            "f_water_1": Field(FieldType.WATER, owner="p1", base_income=0,
                               entity=Entity("ship", 2)),
            "f_island_1": Field(
                FieldType.ISLAND, owner="p2", base_income=1,
                entity=Entity("warrior", 3),
                buildings={"1": Building("ares"), "2": None},
                is_metropolis=True, income=Income(2), neighbors=["f_water_1"],
            ),
        },
    )
    state.cards.hands = {"p1": ["c_minotaur"], "p2": []}
    state.cards.market = ["c_kraken"]
    return state


def test_clone_is_independent():
    original = _sample_state()
    clone = original.clone()

    # mutacja klona nie dotyka oryginału — warunek konieczny dla rolloutów MCTS
    clone.players["p1"].coins = 999
    clone.fields["f_island_1"].entity.quantity = 0
    clone.fields["f_island_1"].buildings["1"].hero = "zeus"
    clone.cards.hands["p1"].append("c_extra")

    assert original.players["p1"].coins == 7
    assert original.fields["f_island_1"].entity.quantity == 3
    assert original.fields["f_island_1"].buildings["1"].hero == "ares"
    assert original.cards.hands["p1"] == ["c_minotaur"]


def test_serialization_roundtrip():
    original = _sample_state()
    restored = GameState.from_dict(original.to_dict())

    # round-trip zachowuje pełną treść stanu
    assert restored.to_dict() == original.to_dict()
    assert restored.stage == Stage.BOARD
    assert restored.fields["f_island_1"].type == FieldType.ISLAND
    assert restored.fields["f_island_1"].buildings["1"].hero == "ares"
    assert restored.players["p1"].priests == 2


def test_to_dict_is_json_serializable():
    import json
    # gdyby coś było nieserializowalne (enum, krotka), json by rzucił — strażnik pod FastAPI
    json.dumps(_sample_state().to_dict())
