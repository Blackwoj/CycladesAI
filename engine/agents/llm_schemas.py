"""Pydantic schematy wyjścia LLM — per bóg i per faza.

Gwarantują walidację i parsowanie odpowiedzi LLM bez ręcznej obsługi błędów.

Użycie:
  schema_for_state(state_view)  → dict (JSON schema do wklejenia w tool definition)
  action_from_llm_output(data, player_id, hero) → Action | None

Każdy schemat odpowiada akcjom dostępnym przy danym bogu.
Discriminator "action_type" mapuje bezpośrednio na silnikowe klasy Action.

Wymaga: pip install pydantic>=2.0
"""
from __future__ import annotations

from typing import Annotated, ClassVar, Literal, Union

# Unconditional import — jeśli pydantic nie jest zainstalowany, moduł rzuca ImportError.
# llm_agent.py łapie to w try/except i wyłącza _SCHEMAS_AVAILABLE.
from pydantic import BaseModel, Field

from ..actions import (
    Action, ApollonBid, BuyCard, Build, EndTurn,
    MoveEntity, PlaceEntity, PlaceIncome, RollBid,
)


# ---- FAZA ROLL (aukcja) ---------------------------------------------------

class RollBidSchema(BaseModel):
    action_type: Literal["roll_bid"]
    row: str = Field(description="Row to bid on: row_1, row_2, row_3, or row_4.")
    amount: int = Field(ge=1, description="Bid amount in coins.")
    reasoning: str = ""

    def to_action(self, player: str) -> RollBid:
        return RollBid(player=player, row=self.row, amount=self.amount)


class ApollonBidSchema(BaseModel):
    action_type: Literal["apollon_bid"]
    reasoning: str = ""

    def to_action(self, player: str) -> ApollonBid:
        return ApollonBid(player=player)


RollPhaseSchema = Annotated[
    Union[RollBidSchema, ApollonBidSchema],
    Field(discriminator="action_type"),
]

# ---- ARES ----------------------------------------------------------------

class PlaceWarriorSchema(BaseModel):
    action_type: Literal["place_entity"]
    field_id: str = Field(description="Island ID to recruit the warrior on (must be yours).")
    quantity: int = Field(default=1, ge=1, le=6)
    reasoning: str = ""

    def to_action(self, player: str) -> PlaceEntity:
        return PlaceEntity(player=player, field_id=self.field_id,
                           kind="warrior", quantity=self.quantity)


class MoveWarriorSchema(BaseModel):
    action_type: Literal["move_entity"]
    from_field: str = Field(description="Source island ID (must have your warriors).")
    to_field: str = Field(description="Destination island ID.")
    quantity: int = Field(default=1, ge=1, le=6)
    reasoning: str = ""

    def to_action(self, player: str) -> MoveEntity:
        return MoveEntity(player=player, from_field=self.from_field,
                          to_field=self.to_field, quantity=self.quantity, kind="warrior")


class _BuildSchema(BaseModel):
    """Budynek boga z tej tury albo metropolia (metropolis=True).

    Jeden schemat na boga, bo w unii z dyskryminatorem `action_type="build"`
    może wystąpić tylko raz.
    """
    HERO: ClassVar[str] = ""   # "" = bóg bez budynku (Apollon) — tylko metropolia

    action_type: Literal["build"]
    field_id: str = Field(description="Your island to build on.")
    metropolis: bool = Field(
        default=False,
        description="True = build a METROPOLIS (needs 4 philosophers or one building of each god).",
    )
    reasoning: str = ""

    def to_action(self, player: str) -> Build:
        hero = "metro" if self.metropolis or not self.HERO else self.HERO
        return Build(player=player, field_id=self.field_id, hero=hero)


class AresBuildSchema(_BuildSchema):
    HERO: ClassVar[str] = "ares"


class EndTurnSchema(BaseModel):
    action_type: Literal["end_turn"]
    reasoning: str = ""

    def to_action(self, player: str) -> EndTurn:
        return EndTurn(player=player)


AresSchema = Annotated[
    Union[PlaceWarriorSchema, MoveWarriorSchema, AresBuildSchema, EndTurnSchema],
    Field(discriminator="action_type"),
]

# ---- POSEJDON ------------------------------------------------------------

class PlaceShipSchema(BaseModel):
    action_type: Literal["place_entity"]
    field_id: str = Field(description="Water tile adjacent to your island to place a ship.")
    quantity: int = Field(default=1, ge=1, le=6)
    reasoning: str = ""

    def to_action(self, player: str) -> PlaceEntity:
        return PlaceEntity(player=player, field_id=self.field_id,
                           kind="ship", quantity=self.quantity)


class MoveShipSchema(BaseModel):
    action_type: Literal["move_entity"]
    from_field: str = Field(description="Source water tile (must have your ships).")
    to_field: str = Field(description="Adjacent water tile to move ships to.")
    quantity: int = Field(default=1, ge=1, le=6)
    reasoning: str = ""

    def to_action(self, player: str) -> MoveEntity:
        return MoveEntity(player=player, from_field=self.from_field,
                          to_field=self.to_field, quantity=self.quantity, kind="ship")


class PosejdonBuildSchema(_BuildSchema):
    HERO: ClassVar[str] = "posejdon"


PosejdonSchema = Annotated[
    Union[PlaceShipSchema, MoveShipSchema, PosejdonBuildSchema, EndTurnSchema],
    Field(discriminator="action_type"),
]

# ---- ATENA ---------------------------------------------------------------

class BuyPhilosopherSchema(BaseModel):
    action_type: Literal["buy_card"]
    hero: Literal["atena"] = "atena"
    reasoning: str = ""

    def to_action(self, player: str) -> BuyCard:
        return BuyCard(player=player, hero="atena")


class AtenaBuildSchema(_BuildSchema):
    HERO: ClassVar[str] = "atena"


AtenaSchema = Annotated[
    Union[BuyPhilosopherSchema, AtenaBuildSchema, EndTurnSchema],
    Field(discriminator="action_type"),
]

# ---- ZEUS ----------------------------------------------------------------

class BuyPriestSchema(BaseModel):
    action_type: Literal["buy_card"]
    hero: Literal["zeus"] = "zeus"
    reasoning: str = ""

    def to_action(self, player: str) -> BuyCard:
        return BuyCard(player=player, hero="zeus")


class ZeusBuildSchema(_BuildSchema):
    HERO: ClassVar[str] = "zeus"


ZeusSchema = Annotated[
    Union[BuyPriestSchema, ZeusBuildSchema, EndTurnSchema],
    Field(discriminator="action_type"),
]

# ---- APOLLON -------------------------------------------------------------

class PlaceIncomeSchema(BaseModel):
    action_type: Literal["place_income"]
    field_id: str = Field(description="Your island to put the +1 income (prosperity) marker on.")
    reasoning: str = ""

    def to_action(self, player: str) -> PlaceIncome:
        return PlaceIncome(player=player, field_id=self.field_id)


class ApollonMetroSchema(_BuildSchema):
    HERO: ClassVar[str] = ""   # Apollon nie ma budynku — "build" = metropolia z kompletu


ApollonSchema = Annotated[
    Union[PlaceIncomeSchema, ApollonMetroSchema, EndTurnSchema],
    Field(discriminator="action_type"),
]

# kolejny gracz na Apollonie: bez znacznika dochodu, ale metropolia z kompletu tak
ApSSchema = Annotated[
    Union[ApollonMetroSchema, EndTurnSchema],
    Field(discriminator="action_type"),
]

# ---------------------------------------------------------------------------
# Wybór akcji w trybie GUIDED (indeks z listy)
# ---------------------------------------------------------------------------

class GuidedChoiceSchema(BaseModel):
    action_index: int = Field(ge=0, description="Index of chosen action from the legal list.")
    reasoning: str = ""


# ---------------------------------------------------------------------------
# Lookup table — hero → schema type annotation
# ---------------------------------------------------------------------------

_HERO_SCHEMA: dict[str, type] = {
    "ares":     AresSchema,     # type: ignore[assignment]
    "posejdon": PosejdonSchema, # type: ignore[assignment]
    "atena":    AtenaSchema,    # type: ignore[assignment]
    "zeus":     ZeusSchema,     # type: ignore[assignment]
    "apollon":  ApollonSchema,   # type: ignore[assignment]
    "ap_s":     ApSSchema,       # type: ignore[assignment]
}

_ROLL_SCHEMA = RollPhaseSchema


# ---------------------------------------------------------------------------
# Publiczne funkcje
# ---------------------------------------------------------------------------

def json_schema_for_hero(hero: str, stage: str = "board") -> dict:
    """Zwróć JSON Schema (dict) odpowiedniego modelu dla danego herosa/fazy."""
    from pydantic import TypeAdapter
    if stage == "roll":
        adapter = TypeAdapter(RollPhaseSchema)  # type: ignore[valid-type]
    else:
        schema_type = _HERO_SCHEMA.get(hero, EndTurnSchema)
        adapter = TypeAdapter(schema_type)      # type: ignore[arg-type]
    return adapter.json_schema()


def action_from_llm_output(data: dict, player: str, hero: str, stage: str = "board") -> Action | None:
    """Waliduj i przekonwertuj surowy dict z LLM na obiekt Action. Zwraca None przy błędzie."""
    from pydantic import TypeAdapter, ValidationError
    if stage == "roll":
        adapter = TypeAdapter(RollPhaseSchema)  # type: ignore[valid-type]
    else:
        schema_type = _HERO_SCHEMA.get(hero, EndTurnSchema)
        adapter = TypeAdapter(schema_type)      # type: ignore[arg-type]
    try:
        parsed = adapter.validate_python(data)
        return parsed.to_action(player)
    except (ValidationError, AttributeError, KeyError, TypeError):
        return None


def guided_choice_from_llm_output(data: dict, num_actions: int) -> int:
    """Waliduj wybór indeksu w trybie GUIDED. Zwraca 0 przy błędzie."""
    from pydantic import ValidationError
    try:
        parsed = GuidedChoiceSchema.model_validate(data)
        idx = parsed.action_index
        return idx if 0 <= idx < num_actions else 0
    except (ValidationError, Exception):
        return 0
