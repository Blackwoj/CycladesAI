"""Jednostki: liczenie, zasięg ruchu, lądowanie i ruch flot (instrukcja str. 4–5).

Wspólne dla akcji bogów (Ares, Posejdon) i Stworów (Pegaz, Sylfida, Syrena).
Funkcje `*_into` mutują przekazany stan — wywołujący daje kopię.
"""
from __future__ import annotations

from ..rng import Rng
from ..state import Entity, FieldType, GameState
from .combat import resolve_battle
from .setup import MAX_UNITS

FLEET_RANGE = 3


# ---------------------------------------------------------------------------
# Liczenie
# ---------------------------------------------------------------------------

def owned_islands(state: GameState, player: str) -> list[str]:
    return sorted(fid for fid, f in state.fields.items()
                  if f.type == FieldType.ISLAND and f.owner == player)


def count_units(state: GameState, player: str, kind: str) -> int:
    ftype = FieldType.ISLAND if kind == "warrior" else FieldType.WATER
    return sum(f.entity.quantity for f in state.fields.values()
               if f.type == ftype and f.owner == player)


def reserve(state: GameState, player: str, kind: str) -> int:
    return MAX_UNITS - count_units(state, player, kind)


def metro_count(state: GameState, player: str) -> int:
    return sum(1 for f in state.fields.values()
               if f.type == FieldType.ISLAND and f.owner == player and f.is_metropolis)


# ---------------------------------------------------------------------------
# Figurki blokujące ruch
# ---------------------------------------------------------------------------

def _figure_field(state: GameState, name: str) -> str | None:
    return state.cards.figures.get(name, {}).get("field")


def water_blocked(state: GameState, field_id: str) -> bool:
    """Floty nie mogą wejść na pole Krakena ani zbliżyć się do wyspy z Polifemem."""
    if field_id == _figure_field(state, "kraken"):
        return True
    poly = _figure_field(state, "polifem")
    return bool(poly) and field_id in state.fields[poly].neighbors


def troops_frozen(state: GameState, island_id: str) -> bool:
    """Meduza: Oddziały na jej wyspie nie mogą się ruszać."""
    return island_id == _figure_field(state, "meduza")


def chiron_protects(state: GameState, island_id: str) -> bool:
    return island_id == _figure_field(state, "chiron")


# ---------------------------------------------------------------------------
# Zasada ostatniej wyspy
# ---------------------------------------------------------------------------

def may_attack_island(state: GameState, attacker: str, island_id: str) -> bool:
    """Nie wolno atakować OSTATNIEJ wyspy gracza, chyba że przejęcie daje wygraną.

    Wejście na pustą wyspę przeciwnika też jest przejęciem, więc podlega zasadzie.
    """
    owner = state.fields[island_id].owner
    if owner is None or owner == attacker:
        return True
    if len(owned_islands(state, owner)) > 1:
        return True
    gain = 1 if state.fields[island_id].is_metropolis else 0
    return metro_count(state, attacker) + gain >= state.options.metros_to_win


# ---------------------------------------------------------------------------
# Zasięg ruchu
# ---------------------------------------------------------------------------

def fleet_chain_targets(state: GameState, from_island: str, player: str) -> list[str]:
    """Wyspy osiągalne z `from_island` łańcuchem WŁASNYCH Flot (Ares, str. 4)."""
    fields = state.fields

    def own_fleet(fid: str) -> bool:
        f = fields.get(fid)
        return bool(f) and f.type == FieldType.WATER and f.owner == player and f.entity.quantity > 0

    frontier = [nb for nb in fields[from_island].neighbors if own_fleet(nb)]
    seen = set(frontier)
    targets: set[str] = set()
    while frontier:
        cur = frontier.pop()
        for nb in fields[cur].neighbors:
            nf = fields.get(nb)
            if nf is None:
                continue
            if nf.type == FieldType.ISLAND:
                if nb != from_island:
                    targets.add(nb)
            elif nb not in seen and own_fleet(nb):
                seen.add(nb)
                frontier.append(nb)
    return sorted(targets)


def fleet_destinations(state: GameState, from_field: str, player: str, max_steps: int = FLEET_RANGE) -> list[str]:
    """Pola morza osiągalne w ≤ max_steps krokach (Posejdon: do 3 pól za 1 GP).

    Ruch przez pola puste lub własne; wejście na pole z cudzymi Flotami kończy
    ruch (bitwa) — takie pole może być tylko celem. Kraken/Polifem blokują.
    """
    fields = state.fields
    dist = {from_field: 0}
    frontier = [from_field]
    out: set[str] = set()
    while frontier:
        nxt = []
        for cur in frontier:
            if dist[cur] >= max_steps:
                continue
            for nb in fields[cur].neighbors:
                nf = fields.get(nb)
                if nf is None or nf.type != FieldType.WATER or nb in dist or water_blocked(state, nb):
                    continue
                dist[nb] = dist[cur] + 1
                out.add(nb)
                enemy = nf.owner not in (None, player) and nf.entity.quantity > 0
                if not enemy:
                    nxt.append(nb)
        frontier = nxt
    out.discard(from_field)
    return sorted(out)


def fleet_recruit_fields(state: GameState, player: str) -> list[str]:
    """Pola morza przy wyspie gracza: puste albo z jego Flotami (str. 4)."""
    out = set()
    for iid in owned_islands(state, player):
        for nb in state.fields[iid].neighbors:
            f = state.fields.get(nb)
            if (f and f.type == FieldType.WATER and f.owner in (None, player)
                    and not water_blocked(state, nb)):
                out.add(nb)
    return sorted(out)


# ---------------------------------------------------------------------------
# Wykonanie ruchu (mutuje stan)
# ---------------------------------------------------------------------------

def _take(state: GameState, from_id: str, qty: int) -> None:
    f = state.fields[from_id]
    f.entity.quantity -= qty
    if f.entity.quantity <= 0:
        f.entity = Entity()
        if f.type == FieldType.WATER:
            f.owner = None          # morze bez flot jest niczyje
        # wyspa zostaje graczowi (znacznik terytorium, str. 4)


def land_troops_into(state: GameState, player: str, from_id: str, to_id: str, qty: int, rng: Rng) -> dict:
    """Przenieś Oddziały na wyspę; cudze Oddziały → bitwa, pusta cudza → przejęcie."""
    _take(state, from_id, qty)
    to_f = state.fields[to_id]
    defended = to_f.owner not in (None, player) and (
        to_f.entity.quantity > 0
        or state.cards.figures.get("minotaur", {}).get("field") == to_id
    )
    if defended:
        return resolve_battle(state, to_id, player, qty, rng)
    to_f.owner = player
    to_f.entity.kind = "warrior"
    to_f.entity.quantity += qty
    return {"combat": False}


def move_fleets_into(state: GameState, player: str, from_id: str, to_id: str, qty: int, rng: Rng) -> dict:
    """Przenieś Floty; pole z cudzymi Flotami → bitwa morska."""
    _take(state, from_id, qty)
    to_f = state.fields[to_id]
    if to_f.owner not in (None, player) and to_f.entity.quantity > 0:
        return resolve_battle(state, to_id, player, qty, rng)
    to_f.owner = player
    to_f.entity.kind = "ship"
    to_f.entity.quantity += qty
    return {"combat": False}
