"""Mitologiczne Stwory (instrukcja str. 3–4, książeczka „Potwory”).

Tor ma 3 pola o koszcie 4 / 3 / 2 GP (slot 0 / 1 / 2). Na początku cyklu:
odrzuć Stwora z pola 2 GP (nieużytego), przesuń resztę w prawo, dociągnij nowe.
W cyklu 1 jest aktywne tylko pole 4 GP, w cyklu 2 — pola 4 i 3 GP.

Wezwać Stwora może gracz każdego boga poza Apollem; każda Świątynia (i
Metropolia) obniża koszt o 1 GP raz na cykl, ale Stwór kosztuje min. 1 GP.
Zeus ma akcję specjalną: za 1 GP wymień Stwora z toru na kartę ze stosu.

Efekt działa natychmiast. W silniku: `BuyCreature` ustawia wybór w toku
(`board.pending`), a cele wskazuje się akcjami `PlayCard(card_id, targets)`.
Każdy efekt da się zakończyć `targets=("done",)` (nic nie robiąc / kończąc
efekt wieloetapowy: Sfinks, Sylfida, ruchy Krakena).

Interpretacje tam, gdzie książeczka jest niejednoznaczna:
- Syrena: „odosobniona Flota” = pole przeciwnika z dokładnie 1 Flotą; gdy nie
  masz Floty w rezerwie, bierzemy ją z Twojego najliczniejszego pola.
- Sylfida: 10 pól = 10 przesunięć grupy Flot o 1 pole.
- Polifem: Floty z pól wokół wyspy odpychamy na pierwsze (wg id) dozwolone pole.
- Figurki (Minotaur, Chiron, Meduza, Polifem) działają do początku następnej
  tury gracza, który ich użył; ich karta wraca na stos odrzuconych wtedy.
  Kraken zostaje na planszy, aż ktoś go znów wezwie (jego karta krąży dalej).
"""
from __future__ import annotations

from ..actions import BuyCreature, PlayCard, ReplaceCreature
from ..rng import Rng
from ..state import FieldType, GameState
from .units import (
    _take,
    chiron_protects,
    count_units,
    land_troops_into,
    may_attack_island,
    move_fleets_into,
    owned_islands,
    reserve,
    troops_frozen,
    water_blocked,
)
from .metro import HEROES_BUILDING, own_buildings, trigger_metropolis

CREATURES = (
    "syrena", "pegaz", "gigant", "chimera", "cyklopi", "sfinks", "sylfida",
    "harpia", "gryf", "mojry", "satyr", "driada",
    "kraken", "minotaur", "chiron", "meduza", "polifem",
)
ISLAND_FIGURES = ("minotaur", "chiron", "meduza", "polifem")
TRACK_COSTS = (4, 3, 2)
SPHINX_PRICE = 2
SYLPH_STEPS = 10
DONE = ("done",)
MAIN_GODS = HEROES_BUILDING   # Ares, Posejdon, Atena, Zeus — bez Apolla


# ---------------------------------------------------------------------------
# Tor Stworów
# ---------------------------------------------------------------------------

def _draw(state: GameState, rng: Rng) -> str | None:
    c = state.cards
    if not c.deck and c.discard:
        c.deck = list(c.discard)
        c.discard = []
        rng.shuffle(c.deck)
    return c.deck.pop(0) if c.deck else None


def update_track(state: GameState, rng: Rng) -> None:
    """Aktualizacja toru na początku cyklu (mutuje stan)."""
    if not state.options.creatures:
        return
    c = state.cards
    active = min(max(state.round_no, 1), len(TRACK_COSTS))
    if c.track[2] is not None:              # nieużyty Stwór z pola 2 GP odpada
        c.discard.append(c.track[2])
        c.track[2] = None
    # przesuń w prawo w obrębie aktywnych pól, potem dociągnij na puste
    cards = [x for x in c.track[:active] if x is not None]
    c.track = [None] * (active - len(cards)) + cards + [None] * (len(TRACK_COSTS) - active)
    for i in range(active):
        if c.track[i] is None:
            c.track[i] = _draw(state, rng)
    c.temple_uses = {}


def temples(state: GameState, player: str) -> int:
    """Świątynie + Metropolie (Metropolia ma funkcje wszystkich budynków)."""
    n = 0
    for f in state.fields.values():
        if f.type == FieldType.ISLAND and f.owner == player:
            n += sum(1 for b in f.buildings.values() if b and b.hero == "zeus")
            n += 1 if f.is_metropolis else 0
    return n


def creature_cost(state: GameState, player: str, slot: int) -> tuple[int, int]:
    """(koszt, użyta_zniżka) — zniżka ze Świątyń raz na cykl, min. 1 GP."""
    base = TRACK_COSTS[slot]
    free = max(0, temples(state, player) - state.cards.temple_uses.get(player, 0))
    discount = min(free, base - 1)
    return base - discount, discount


# ---------------------------------------------------------------------------
# Kupno / wymiana (akcje tury)
# ---------------------------------------------------------------------------

def legal_creature_actions(state: GameState) -> list:
    if not state.options.creatures or state.act_hero not in MAIN_GODS:
        return []
    pid = state.act_player
    coins = state.players[pid].coins
    out: list = []
    for slot, card in enumerate(state.cards.track):
        if card is None:
            continue
        if creature_cost(state, pid, slot)[0] <= coins:
            out.append(BuyCreature(player=pid, slot=slot))
        if state.act_hero == "zeus" and coins >= 1 and (state.cards.deck or state.cards.discard):
            out.append(ReplaceCreature(player=pid, slot=slot))
    return out


def apply_replace(s: GameState, action: ReplaceCreature, rng: Rng) -> dict:
    if s.act_hero != "zeus" or s.cards.track[action.slot] is None or s.players[action.player].coins < 1:
        return {"valid": False, "reason": "nie można wymienić Stwora"}
    s.players[action.player].coins -= 1
    s.cards.discard.append(s.cards.track[action.slot])
    s.cards.track[action.slot] = _draw(s, rng)
    return {"valid": True}


def apply_buy(s: GameState, action: BuyCreature, rng: Rng) -> dict:
    pid, slot = action.player, action.slot
    card = s.cards.track[slot] if 0 <= slot < len(TRACK_COSTS) else None
    if card is None or s.act_hero not in MAIN_GODS:
        return {"valid": False, "reason": "brak Stwora na tym polu"}
    cost, discount = creature_cost(s, pid, slot)
    if s.players[pid].coins < cost:
        return {"valid": False, "reason": "brak złota na Stwora"}
    s.players[pid].coins -= cost
    s.cards.temple_uses[pid] = s.cards.temple_uses.get(pid, 0) + discount
    s.cards.track[slot] = None
    # karta figurki na wyspie wraca na stos dopiero ze zdjęciem figurki
    if card not in ISLAND_FIGURES and card != "chimera":
        s.cards.discard.append(card)
    _start_effect(s, pid, card)
    return {"valid": True, "creature": card, "cost": cost}


def _start_effect(s: GameState, pid: str, card: str) -> None:
    if card == "mojry":                      # natychmiastowy dochód — bez wyboru
        from .scoring import calculate_income
        s.players[pid].coins += calculate_income(s)[pid]
        trigger_metropolis(s, pid)
        return
    s.board.pending = {"kind": "creature", "card": card}
    if card == "sylfida":
        s.board.pending["budget"] = SYLPH_STEPS


# ---------------------------------------------------------------------------
# Rozstrzyganie efektu — legalne cele
# ---------------------------------------------------------------------------

def _others(state: GameState, pid: str) -> list[str]:
    return [p for p in state.players if p != pid]


def pending_actions(state: GameState) -> list[PlayCard]:
    pending = state.board.pending or {}
    card, pid = pending.get("card"), state.act_player
    targets: list[tuple] = []
    f = state.fields

    if card == "syrena":
        targets = [(fid,) for fid, x in sorted(f.items())
                   if x.type == FieldType.WATER and x.owner not in (None, pid) and x.entity.quantity == 1]
    elif card == "pegaz":
        for src in owned_islands(state, pid):
            n = f[src].entity.quantity
            if n == 0 or troops_frozen(state, src):
                continue
            for dst, x in sorted(f.items()):
                if dst == src or x.type != FieldType.ISLAND:
                    continue
                if x.owner != pid and (chiron_protects(state, dst) or not may_attack_island(state, pid, dst)):
                    continue
                targets += [(src, dst, q) for q in range(1, n + 1)]
    elif card == "gigant":
        targets = [(fid, slot) for fid, x in sorted(f.items())
                   if x.type == FieldType.ISLAND and not x.is_metropolis and not chiron_protects(state, fid)
                   for slot, b in x.buildings.items() if b]
    elif card == "chimera":
        targets = [(c,) for c in sorted(set(state.cards.discard)) if c != "chimera"]
    elif card == "cyklopi":
        targets = [(fid, slot, h) for fid, slot, cur in own_buildings(state, pid)
                   for h in HEROES_BUILDING if h != cur]
    elif card == "sfinks":
        p = state.players[pid]
        targets = [("warrior", fid) for fid in owned_islands(state, pid) if f[fid].entity.quantity > 0]
        targets += [("ship", fid) for fid, x in sorted(f.items())
                    if x.type == FieldType.WATER and x.owner == pid and x.entity.quantity > 0]
        targets += [("priest",)] if p.priests else []
        targets += [("philosopher",)] if p.philosophers else []
    elif card == "sylfida":
        if pending.get("budget", 0) > 0:
            for src, x in sorted(f.items()):
                if x.type != FieldType.WATER or x.owner != pid or x.entity.quantity == 0:
                    continue
                for dst in x.neighbors:
                    y = f.get(dst)
                    if y is None or y.type != FieldType.WATER or water_blocked(state, dst):
                        continue
                    targets += [(src, dst, q) for q in range(1, x.entity.quantity + 1)]
    elif card == "harpia":
        targets = [(fid,) for fid, x in sorted(f.items())
                   if x.type == FieldType.ISLAND and x.owner not in (None, pid)
                   and x.entity.quantity > 0 and not chiron_protects(state, fid)]
    elif card == "gryf":
        targets = [(p,) for p in _others(state, pid) if state.players[p].coins > 1]
    elif card == "satyr":
        targets = [(p,) for p in _others(state, pid) if state.players[p].philosophers > 0]
    elif card == "driada":
        targets = [(p,) for p in _others(state, pid) if state.players[p].priests > 0]
    elif card == "kraken":
        at = pending.get("kraken_at")
        if at is None:
            targets = [(fid,) for fid, x in sorted(f.items()) if x.type == FieldType.WATER]
        elif state.players[pid].coins >= 1:      # każde dodatkowe GP = 1 pole dalej
            targets = [(nb,) for nb in sorted(f[at].neighbors) if f.get(nb) and f[nb].type == FieldType.WATER]
    elif card in ISLAND_FIGURES:
        targets = [(fid,) for fid, x in sorted(f.items()) if x.type == FieldType.ISLAND]

    return [PlayCard(player=pid, card_id=card, targets=t) for t in targets] + [
        PlayCard(player=pid, card_id=card, targets=DONE)]


# ---------------------------------------------------------------------------
# Rozstrzyganie efektu — wykonanie
# ---------------------------------------------------------------------------

def apply_play(s: GameState, action: PlayCard, rng: Rng) -> dict:
    """Wykonaj wybrany cel (mutuje kopię stanu podaną przez silnik)."""
    if action not in pending_actions(s):
        return {"valid": False, "reason": "nieprawidłowy cel Stwora"}
    pid, card, t = action.player, action.card_id, tuple(action.targets)
    info: dict = {"valid": True, "creature": card}
    finished = True

    if t == DONE:
        if card == "chimera":
            _reshuffle_after_chimera(s, rng)
    elif card == "syrena":
        if reserve(s, pid, "ship") == 0:
            src = sorted((fid for fid, x in s.fields.items()
                          if x.type == FieldType.WATER and x.owner == pid and x.entity.quantity > 0),
                         key=lambda fid: (-s.fields[fid].entity.quantity, fid))[0]
            _take(s, src, 1)
        x = s.fields[t[0]]
        x.owner, x.entity.kind, x.entity.quantity = pid, "ship", 1
    elif card == "pegaz":
        info.update(land_troops_into(s, pid, t[0], t[1], t[2], rng))
    elif card == "gigant":
        s.fields[t[0]].buildings[t[1]] = None
    elif card == "chimera":
        _reshuffle_after_chimera(s, rng)
        _start_effect(s, pid, t[0])                  # moc wybranego Stwora, bez płacenia
        finished = False
        info["chimera_as"] = t[0]
    elif card == "cyklopi":
        from ..state import Building
        s.fields[t[0]].buildings[t[1]] = Building(t[2])
    elif card == "sfinks":
        _sell(s, pid, t)
        finished = False
    elif card == "sylfida":
        info.update(move_fleets_into(s, pid, t[0], t[1], t[2], rng))
        s.board.pending["budget"] -= 1
        finished = False
    elif card == "harpia":
        x = s.fields[t[0]]
        x.entity.quantity -= 1
        if x.entity.quantity == 0:
            x.entity.kind = None            # wyspa zostaje właścicielowi
    elif card == "gryf":
        loot = s.players[t[0]].coins // 2
        s.players[t[0]].coins -= loot
        s.players[pid].coins += loot
        info["loot"] = loot
    elif card == "satyr":
        s.players[t[0]].philosophers -= 1
        s.players[pid].philosophers += 1
    elif card == "driada":
        s.players[t[0]].priests -= 1
        s.players[pid].priests += 1
    elif card == "kraken":
        if s.board.pending.get("kraken_at") is not None:
            s.players[pid].coins -= 1
        _kraken_to(s, t[0])
        s.board.pending["kraken_at"] = t[0]
        finished = False
    elif card in ISLAND_FIGURES:
        _place_figure(s, pid, card, t[0])

    if finished and s.board.pending is not None and s.board.pending.get("card") == card:
        s.board.pending = None
    if s.board.pending is None:
        trigger_metropolis(s, pid)
    return info


def _sell(s: GameState, pid: str, t: tuple) -> None:
    p = s.players[pid]
    if t[0] in ("warrior", "ship"):
        x = s.fields[t[1]]
        x.entity.quantity -= 1
        if x.entity.quantity == 0:
            x.entity.kind = None
            if x.type == FieldType.WATER:
                x.owner = None
    elif t[0] == "priest":
        p.priests -= 1
    else:
        p.philosophers -= 1
    p.coins += SPHINX_PRICE


def _reshuffle_after_chimera(s: GameState, rng: Rng) -> None:
    """Chimera na stosie odrzuconych → potasuj odrzucone razem ze stosem dobierania."""
    c = s.cards
    c.deck = c.deck + c.discard + ["chimera"]
    c.discard = []
    rng.shuffle(c.deck)


def _kraken_to(s: GameState, fid: str) -> None:
    """Kraken niszczy wszystkie Floty na polu (wracają do rezerwy)."""
    s.cards.figures["kraken"] = {"field": fid, "owner": s.act_player}
    x = s.fields[fid]
    if x.entity.quantity:
        x.entity.quantity = 0
        x.entity.kind = None
        x.owner = None


def _place_figure(s: GameState, pid: str, card: str, island: str) -> None:
    figs = s.cards.figures
    # dwie figurki na jednej wyspie niszczą się wzajemnie
    clash = [name for name, fig in figs.items()
             if name in ISLAND_FIGURES and name != card and fig.get("field") == island]
    if clash:
        for name in clash:
            remove_figure(s, name)
        s.cards.discard.append(card)
        return
    if card in figs:
        remove_figure(s, card)
    figs[card] = {"field": island, "owner": pid}
    if card == "polifem":
        _polyphemus_push(s, island)


def remove_figure(s: GameState, name: str) -> None:
    if s.cards.figures.pop(name, None) is not None and name in ISLAND_FIGURES:
        s.cards.discard.append(name)


def expire_figures(s: GameState, player: str) -> None:
    """Figurki na wyspach działają do początku następnej tury ich właściciela."""
    for name in [n for n, fig in s.cards.figures.items()
                 if n in ISLAND_FIGURES and fig.get("owner") == player]:
        remove_figure(s, name)


def _polyphemus_push(s: GameState, island: str) -> None:
    """Odepchnij Floty z pól wokół wyspy o 1 pole (albo zniszcz, gdy się nie da)."""
    ring = {nb for nb in s.fields[island].neighbors if s.fields.get(nb) and s.fields[nb].type == FieldType.WATER}
    for fid in sorted(ring):
        x = s.fields[fid]
        if x.entity.quantity == 0:
            continue
        owner, qty = x.owner, x.entity.quantity
        dest = next((nb for nb in sorted(x.neighbors)
                     if nb not in ring and s.fields.get(nb) and s.fields[nb].type == FieldType.WATER
                     and s.fields[nb].owner in (None, owner)
                     and nb != s.cards.figures.get("kraken", {}).get("field")), None)
        x.entity.quantity, x.entity.kind, x.owner = 0, None, None
        if dest is not None:
            y = s.fields[dest]
            y.owner, y.entity.kind = owner, "ship"
            y.entity.quantity += qty


# używane przez board.py przy rekrutacji (Floty nie wchodzą na pole Krakena)
__all__ = [
    "CREATURES", "ISLAND_FIGURES", "TRACK_COSTS", "update_track", "legal_creature_actions",
    "apply_buy", "apply_replace", "pending_actions", "apply_play", "expire_figures",
    "creature_cost", "temples", "count_units",
]
