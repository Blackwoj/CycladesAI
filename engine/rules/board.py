"""Reguły fazy BOARD — tury graczy (instrukcja str. 3–6, książeczka str. 4).

Moce bogów:
- Posejdon: rekrutuj 1–4 Floty (1. darmowa, potem 1/2/3 GP), Port, ruch Flot
  z jednego pola o ≤ 3 pola za 1 GP;
- Ares: rekrutuj 1–4 Oddziały (1. darmowy, potem 2/3/4 GP), Forteca, ruch
  Oddziałów z wyspy na wyspę po łańcuchu własnych Flot za 1 GP;
- Zeus: 1 darmowy Kapłan (+1 za 4 GP), Świątynia, wymiana Stwora za 1 GP;
- Atena: 1 darmowy Filozof (+1 za 4 GP), Uniwersytet;
- Apollo: 1 GP (4 GP przy ≤ 1 wyspie), pierwszy gracz kładzie znacznik dobrobytu.
Każdy bóg poza Apollem może wzywać Stwory (engine/rules/creatures.py).
Budynek kosztuje 2 GP; limit jednostek na planszy: 8 Oddziałów i 8 Flot.

Wszystkie funkcje czyste: (state, action) → state'.
"""
from __future__ import annotations

import copy

from ..actions import (
    Action, Build, BuyCard, BuyCreature, EndTurn, MoveEntity, PlaceEntity, PlaceIncome,
    PlayCard, ReplaceCreature,
)
from ..rng import Rng
from ..state import Building, BoardPhaseState, FieldType, GameState
from . import creatures
from .metro import HEROES_BUILDING, metro_actions, place_metropolis, trigger_metropolis
from .setup import MAX_UNITS, SHIP_PRICING, WARRIOR_PRICING
from .units import (
    count_units,
    fleet_chain_targets,
    fleet_destinations,
    fleet_recruit_fields,
    land_troops_into,
    may_attack_island,
    move_fleets_into,
    owned_islands,
    troops_frozen,
)

_BUILD_COST = 2
_CARD_COST = 4
_MAX_RECRUITS = len(WARRIOR_PRICING)    # 1 darmowy + 3 dokupione na turę


# ---------------------------------------------------------------------------
# Przejście do tury konkretnego gracza
# ---------------------------------------------------------------------------

def start_player_turn(state: GameState) -> GameState:
    """Pobierz następną turę z play_order (+ play_heroes) i zainicjalizuj ją."""
    s = copy.deepcopy(state)
    if not s.play_order:
        return s   # faza BOARD skończona — wywoła end_board_phase
    s.act_player = s.play_order[0]
    s.play_order = s.play_order[1:]
    if s.play_heroes:
        s.act_hero = s.play_heroes[0]
        s.play_heroes = s.play_heroes[1:]
    else:
        s.act_hero = s.hero_players.get(s.act_player, "None")
    s.hero_players[s.act_player] = s.act_hero

    s.board = BoardPhaseState()
    creatures.expire_figures(s, s.act_player)

    # Darmowe efekty boga
    hero, player = s.act_hero, s.players[s.act_player]
    if hero == "atena":
        player.philosophers += 1
        s.board.athena_card = True
    elif hero == "zeus":
        player.priests += 1
        s.board.zeus_card = True
    elif hero in ("apollon", "ap_s"):
        player.coins += 1 if len(owned_islands(s, s.act_player)) > 1 else 4
        s.board.apollon_income = hero == "apollon"   # znacznik tylko dla pierwszego

    trigger_metropolis(s, s.act_player)               # np. 4. Filozof od Ateny
    return s


# ---------------------------------------------------------------------------
# Legalne akcje — BOARD
# ---------------------------------------------------------------------------

def legal_board_actions(state: GameState) -> list[Action]:
    """Legalne akcje dla act_player w fazie BOARD zależne od herosa."""
    hero, pid = state.act_hero, state.act_player
    if pid is None or hero is None:
        return []

    pending = state.board.pending
    if pending:
        if pending["kind"] == "metropolis":
            return metro_actions(state)
        return creatures.pending_actions(state)

    actions: list[Action] = []
    if hero == "ares":
        actions += _recruit_actions(state, "warrior")
        actions += _ares_moves(state)
    elif hero == "posejdon":
        actions += _recruit_actions(state, "ship")
        actions += _poseidon_moves(state)
    elif hero in ("atena", "zeus"):
        if state.players[pid].coins >= _CARD_COST and (
                state.board.athena_card if hero == "atena" else state.board.zeus_card):
            actions.append(BuyCard(player=pid, hero=hero))
    elif hero == "apollon" and state.board.apollon_income:
        actions += [PlaceIncome(player=pid, field_id=fid) for fid in owned_islands(state, pid)]

    actions += _build_actions(state)
    actions += creatures.legal_creature_actions(state)
    actions.append(EndTurn(player=pid))
    return actions


def _recruit_price(state: GameState, kind: str) -> int | None:
    n = state.board.entity_price
    if n >= _MAX_RECRUITS:
        return None
    return (WARRIOR_PRICING if kind == "warrior" else SHIP_PRICING)[n]


def _recruit_actions(state: GameState, kind: str) -> list[Action]:
    pid = state.act_player
    price = _recruit_price(state, kind)
    if price is None or state.players[pid].coins < price or count_units(state, pid, kind) >= MAX_UNITS:
        return []
    fields = owned_islands(state, pid) if kind == "warrior" else fleet_recruit_fields(state, pid)
    return [PlaceEntity(player=pid, field_id=fid, kind=kind, quantity=1) for fid in fields]


def _ares_moves(state: GameState) -> list[Action]:
    pid = state.act_player
    if state.players[pid].coins < 1:
        return []
    out: list[Action] = []
    for src in owned_islands(state, pid):
        n = state.fields[src].entity.quantity
        if n == 0 or troops_frozen(state, src):
            continue
        for dst in fleet_chain_targets(state, src, pid):
            if not may_attack_island(state, pid, dst):
                continue
            out += [MoveEntity(player=pid, from_field=src, to_field=dst, quantity=q) for q in range(1, n + 1)]
    return out


def _poseidon_moves(state: GameState) -> list[Action]:
    pid = state.act_player
    if state.players[pid].coins < 1:
        return []
    out: list[Action] = []
    for src, f in sorted(state.fields.items()):
        if f.type != FieldType.WATER or f.owner != pid or f.entity.quantity == 0 or f.entity.kind != "ship":
            continue
        for dst in fleet_destinations(state, src, pid):
            out += [MoveEntity(player=pid, from_field=src, to_field=dst, quantity=q)
                    for q in range(1, f.entity.quantity + 1)]
    return out


def _build_actions(state: GameState) -> list[Build]:
    """Budynek boga z tej tury (2 GP) na własnej wyspie z wolnym miejscem."""
    pid, hero = state.act_player, state.act_hero
    if hero not in HEROES_BUILDING or state.players[pid].coins < _BUILD_COST:
        return []
    return [Build(player=pid, field_id=fid, hero=hero)
            for fid in owned_islands(state, pid)
            if not state.fields[fid].is_metropolis
            and any(b is None for b in state.fields[fid].buildings.values())]


def validate_action(state: GameState, action: Action) -> bool:
    """Czy akcja jest legalna (przynależność do legal_board_actions)."""
    return action in legal_board_actions(state)


# ---------------------------------------------------------------------------
# Aplikacja akcji — BOARD
# ---------------------------------------------------------------------------

def apply_board_action(state: GameState, action: Action, rng: Rng) -> tuple[GameState, dict]:
    """Zastosuj akcję. Zwraca (nowy_stan, info). Nie mutuje wejścia."""
    if state.board.pending and action not in legal_board_actions(state):
        return state, {"valid": False, "reason": "najpierw rozstrzygnij wybór w toku"}
    s = copy.deepcopy(state)
    info = _dispatch(s, action, rng)
    if not info.get("valid"):
        return state, info
    # walka/Stwór/budowa mogły domknąć warunek metropolii — jest obowiązkowa
    trigger_metropolis(s, s.act_player)
    return s, info


def _dispatch(s: GameState, action: Action, rng: Rng) -> dict:
    if isinstance(action, PlaceEntity):
        return _apply_place_entity(s, action)
    if isinstance(action, MoveEntity):
        return _move(s, action, rng)
    if isinstance(action, Build):
        return _apply_build(s, action)
    if isinstance(action, BuyCard):
        return _apply_buy_card(s, action)
    if isinstance(action, PlaceIncome):
        return _apply_place_income(s, action)
    if isinstance(action, BuyCreature):
        return creatures.apply_buy(s, action, rng)
    if isinstance(action, ReplaceCreature):
        return creatures.apply_replace(s, action, rng)
    if isinstance(action, PlayCard):
        if not s.board.pending or s.board.pending.get("kind") != "creature":
            return {"valid": False, "reason": "brak Stwora do rozstrzygnięcia"}
        return creatures.apply_play(s, action, rng)
    if isinstance(action, EndTurn):
        return _apply_end_turn(s)
    raise ValueError(f"Nieznana akcja: {action}")


def _apply_place_entity(s: GameState, action: PlaceEntity) -> dict:
    if s.act_hero != ("ares" if action.kind == "warrior" else "posejdon"):
        return {"valid": False, "reason": "rekrutacja wymaga Aresa/Posejdona"}
    if PlaceEntity(player=action.player, field_id=action.field_id, kind=action.kind, quantity=1) \
            not in _recruit_actions(s, action.kind):
        return {"valid": False, "reason": "rekrutacja niedozwolona (złoto, limit, pole)"}
    s.players[action.player].coins -= _recruit_price(s, action.kind)
    field = s.fields[action.field_id]
    field.entity.quantity += 1
    field.entity.kind = action.kind
    field.owner = action.player
    s.board.entity_price += 1
    return {"valid": True}


def _move(s: GameState, action: MoveEntity, rng: Rng) -> dict:
    """Ruch Oddziałów (Ares) albo Flot (Posejdon) — 1 GP."""
    legal = _ares_moves(s) if s.act_hero == "ares" else _poseidon_moves(s) if s.act_hero == "posejdon" else []
    plain = MoveEntity(player=action.player, from_field=action.from_field,
                       to_field=action.to_field, quantity=action.quantity)
    if plain not in legal:
        return {"valid": False, "reason": "ruch niedozwolony"}
    s.players[action.player].coins -= 1
    mover = land_troops_into if s.act_hero == "ares" else move_fleets_into
    return {"valid": True, **mover(s, action.player, action.from_field, action.to_field, action.quantity, rng)}


# zgodność wsteczna z testami regresyjnymi (ta sama ścieżka co step())
def _apply_move_entity(state: GameState, action: MoveEntity, rng: Rng) -> tuple[GameState, dict]:
    return apply_board_action(state, action, rng)


def _apply_build(s: GameState, action: Build) -> dict:
    if action.hero == "metro":
        return place_metropolis(s, action.player, action.field_id)
    if action not in _build_actions(s):
        return {"valid": False, "reason": "budowa niedozwolona (bóg, złoto, wolne miejsce)"}
    field = s.fields[action.field_id]
    slot = next(sl for sl, b in field.buildings.items() if b is None)
    field.buildings[slot] = Building(hero=action.hero)
    s.players[action.player].coins -= _BUILD_COST
    return {"valid": True}


def _apply_buy_card(s: GameState, action: BuyCard) -> dict:
    if action not in legal_board_actions(s):
        return {"valid": False, "reason": "zakup karty niedozwolony"}
    player = s.players[action.player]
    player.coins -= _CARD_COST
    if action.hero == "atena":
        player.philosophers += 1
        s.board.athena_card = False
    else:
        player.priests += 1
        s.board.zeus_card = False
    return {"valid": True}


def _apply_place_income(s: GameState, action: PlaceIncome) -> dict:
    if action not in legal_board_actions(s):
        return {"valid": False, "reason": "znacznik dochodu niedozwolony"}
    s.fields[action.field_id].income.quantity += 1
    s.board.apollon_income = False
    return {"valid": True}


def _apply_end_turn(s: GameState) -> dict:
    # znacznik ofiarowania na tor kolejności: kto kończy później, licytuje wcześniej
    s.acted.append(s.act_player)
    s.act_player = None
    s.act_hero = None
    # Kolejnego gracza uruchomi engine.step po sprawdzeniu play_order
    return {"valid": True, "end_turn": True}
