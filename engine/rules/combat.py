"""Bitwy (instrukcja str. 5).

Każda runda bitwy: obie strony liczą siłę = jednostki + rzut kością (+ bonusy
obrońcy). Niższy wynik traci 1 jednostkę, remis — obie strony tracą po 1.
Powtarzamy, aż na polu zostanie jedna strona.

- kość specjalna Cyclades ma ścianki 0,0,1,1,2,3;
- `GameOptions.combat_dice=False` → kość zawsze 0 (wariant deterministyczny,
  ta sama procedura, tylko bez losowości — tańszy dla MCTS);
- obrona na wyspie: +1 za każdą Fortecę na tej wyspie, Metropolia liczy się
  jak Forteca (ma funkcje wszystkich budynków);
- obrona na morzu: +1 za każdy Port na wyspach obrońcy sąsiadujących z polem
  (Metropolia jak Port);
- Minotaur na wyspie: obrońca +2 do siły; ginie dopiero po zwykłych Oddziałach;
- wycofanie się z bitwy (decyzja w trakcie walki) NIE jest modelowane —
  bitwa toczy się do końca. Świadome uproszczenie.
"""
from __future__ import annotations

from ..rng import Rng
from ..state import FieldType, GameState

DIE_FACES = (0, 0, 1, 1, 2, 3)


def _roll(state: GameState, rng: Rng) -> int:
    return rng.choice(DIE_FACES) if state.options.combat_dice else 0


def defence_bonus(state: GameState, field_id: str, defender: str) -> int:
    field = state.fields[field_id]
    if field.type == FieldType.ISLAND:
        forts = sum(1 for b in field.buildings.values() if b and b.hero == "ares")
        return forts + (1 if field.is_metropolis else 0)
    bonus = 0
    for nb in field.neighbors:
        isl = state.fields.get(nb)
        if isl is None or isl.type != FieldType.ISLAND or isl.owner != defender:
            continue
        bonus += sum(1 for b in isl.buildings.values() if b and b.hero == "posejdon")
        bonus += 1 if isl.is_metropolis else 0
    return bonus


def resolve_battle(
    state: GameState, field_id: str, attacker: str, attackers: int, rng: Rng,
) -> dict:
    """Rozegraj bitwę o `field_id` (mutuje `state`). Zwraca info do logu.

    Wywołujący odjął już `attackers` z pola źródłowego. Jednostki atakującego
    lądują na polu tylko, jeśli wygra.
    """
    field = state.fields[field_id]
    defender = field.owner
    kind = "warrior" if field.type == FieldType.ISLAND else "ship"
    defenders = field.entity.quantity
    minotaur = (
        kind == "warrior"
        and state.cards.figures.get("minotaur", {}).get("field") == field_id
    )
    bonus = defence_bonus(state, field_id, defender)
    rounds = 0

    while attackers > 0 and (defenders > 0 or minotaur):
        rounds += 1
        att = attackers + _roll(state, rng)
        dfn = defenders + (2 if minotaur else 0) + bonus + _roll(state, rng)
        att_loses = att <= dfn
        def_loses = dfn <= att
        if att_loses:
            attackers -= 1
        if def_loses:
            if defenders > 0:
                defenders -= 1
            else:
                minotaur = False
                state.cards.figures.pop("minotaur", None)

    if attackers > 0:
        field.owner = attacker
        field.entity.kind = kind
        field.entity.quantity = attackers
        winner = attacker
    else:
        field.entity.quantity = defenders
        if defenders == 0:
            field.entity.kind = None
            if kind == "ship":
                field.owner = None      # morze bez flot jest niczyje
        # na lądzie obrońca zachowuje wyspę nawet bez Oddziałów (instrukcja str. 5)
        winner = defender
    return {"combat": True, "winner": winner, "rounds": rounds,
            "attackers_left": attackers, "defenders_left": defenders}
