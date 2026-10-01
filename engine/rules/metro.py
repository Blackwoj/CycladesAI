"""Metropolie (instrukcja str. 6, książeczka str. 4).

Metropolia powstaje NATYCHMIAST i obowiązkowo, gdy gracz:
- zdobędzie czwartego Filozofa → odrzuca 4 Filozofów, albo
- ma po 1 budynku każdego z 4 bogów (na 1 lub kilku wyspach) → zdejmuje je.

Silnik modeluje to jako wybór w toku (`board.pending`): dopóki gracz nie wskaże
wyspy, jedyne legalne akcje to `Build(hero="metro", field_id=...)`.
"""
from __future__ import annotations

from ..actions import Build
from ..state import FieldType, GameState

PHILOSOPHERS_FOR_METRO = 4
HEROES_BUILDING = ("ares", "posejdon", "atena", "zeus")


def own_buildings(state: GameState, player_id: str) -> list[tuple[str, str, str]]:
    """(field_id, slot, hero) budynków na wyspach gracza, poza metropoliami."""
    return [
        (fid, slot, b.hero)
        for fid, f in state.fields.items()
        if f.type == FieldType.ISLAND and f.owner == player_id and not f.is_metropolis
        for slot, b in f.buildings.items() if b
    ]


def has_building_set(state: GameState, player_id: str) -> bool:
    return set(HEROES_BUILDING).issubset({h for _, _, h in own_buildings(state, player_id)})


def metro_sites(state: GameState, player_id: str) -> list[str]:
    return sorted(fid for fid, f in state.fields.items()
                  if f.type == FieldType.ISLAND and f.owner == player_id and not f.is_metropolis)


def trigger_metropolis(state: GameState, player_id: str | None) -> None:
    """Jeśli gracz spełnia warunek — ustaw obowiązkowy wybór miejsca (mutuje stan).

    Nie nadpisuje innego wyboru w toku (np. efektu Stwora) — zostanie sprawdzone
    ponownie po jego rozstrzygnięciu.
    """
    if player_id is None or state.board.pending is not None:
        return
    player = state.players[player_id]
    if player.philosophers >= PHILOSOPHERS_FOR_METRO:
        player.philosophers -= PHILOSOPHERS_FOR_METRO
        source = "philosophers"
    elif has_building_set(state, player_id):
        source = "buildings"
    else:
        return
    if metro_sites(state, player_id):
        state.board.pending = {"kind": "metropolis", "source": source}
    # brak wyspy pod metropolię: filozofowie przepadają, budynki zostają


def metro_actions(state: GameState) -> list[Build]:
    pid = state.act_player
    return [Build(player=pid, field_id=fid, hero="metro") for fid in metro_sites(state, pid)]


def place_metropolis(state: GameState, player_id: str, field_id: str) -> dict:
    """Postaw metropolię z wyboru w toku (mutuje stan)."""
    pending = state.board.pending or {}
    if pending.get("kind") != "metropolis":
        return {"valid": False, "reason": "brak prawa do metropolii"}
    if field_id not in metro_sites(state, player_id):
        return {"valid": False, "reason": "nie można tu postawić metropolii"}
    source = pending["source"]
    if source == "buildings":
        _consume_building_set(state, player_id, field_id)
    state.fields[field_id].is_metropolis = True
    state.board.pending = None
    return {"valid": True, "metropolis": True, "source": source}


def _consume_building_set(state: GameState, player_id: str, target_field: str) -> None:
    """Zdejmij po jednym budynku każdego boga (metropolia je „wchłania”).

    Kolejność deterministyczna: najpierw budynki z wyspy docelowej, potem po id
    pola i slotu — bez dokładania gałęzi wyboru do legal_actions.
    """
    owned = sorted(own_buildings(state, player_id), key=lambda x: (x[0] != target_field, x[0], x[1]))
    for hero in HEROES_BUILDING:
        fid, slot, _ = next(b for b in owned if b[2] == hero)
        state.fields[fid].buildings[slot] = None
