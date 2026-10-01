"""Reguły fazy ROLL — składanie ofiar (licytacja bogów).

Zgodnie z instrukcją (str. 2–3, 6):
- w kolejności toru każdy znacznik ofiarowania trafia do jednego boga;
- przebicie wymaga wyższej ofiary, a przelicytowany gracz NATYCHMIAST licytuje
  u INNEGO boga (nie może wrócić do tego, którego stracił);
- Apollo jest darmowy i mieści wielu graczy (pierwszy dostaje znacznik dobrobytu);
- ofiar nie wolno składać ponad stan: suma kosztów (po zniżce Kapłanów, min. 1 GP
  za ofiarę) nie może przekroczyć złota gracza;
- w grze 2-osobowej każdy ma 2 znaczniki i ofiaruje DWÓM różnym bogom,
  a w grze są 3 bogowie + Apollo (zasady jak dla 4 graczy).

Funkcje są czyste (state in → state' out) — wejście nigdy nie jest mutowane.
"""
from __future__ import annotations

import copy

from ..actions import ApollonBid, RollBid
from ..rng import Rng
from ..state import GameState, Player, Stage

HEROES_BIDDABLE = ["ares", "atena", "posejdon", "zeus"]
APOLLO_ROW = "row_5"


# ---------------------------------------------------------------------------
# Pomocnicze
# ---------------------------------------------------------------------------

def markers_per_player(state: GameState) -> int:
    return 2 if state.num_of_players == 2 else 1


def visible_gods(num_players: int) -> int:
    """Ilu bogów (poza Apollem) jest w licytacji: 2p gra jak 4p."""
    return 3 if num_players == 2 else num_players - 1


def _bid_cost(bid_amount: int, player: Player) -> int:
    """Rzeczywisty koszt ofiary (Kapłani są zniżką, min 1 GP)."""
    return max(bid_amount - player.priests, 1)


def _rows_of(state: GameState, player_id: str) -> list[str]:
    """Rzędy, w których gracz ma teraz znacznik."""
    rows = [r for r, b in state.roll.bids.items() if r != APOLLO_ROW and b and b.get("player") == player_id]
    rows += [APOLLO_ROW] * state.roll.bids.get(APOLLO_ROW, []).count(player_id)
    return rows


def _committed_cost(state: GameState, player_id: str, except_row: str | None = None) -> int:
    player = state.players[player_id]
    return sum(
        _bid_cost(b["bid"], player)
        for r, b in state.roll.bids.items()
        if r != APOLLO_ROW and r != except_row and b and b.get("player") == player_id
    )


# ---------------------------------------------------------------------------
# Legalne akcje
# ---------------------------------------------------------------------------

def legal_roll_actions(state: GameState) -> list:
    """Legalne akcje dla act_player w fazie ROLL."""
    player_id = state.act_player
    if player_id is None:
        return []
    player = state.players[player_id]
    banned = set(state.roll.banned.get(player_id, []))
    mine = _rows_of(state, player_id)
    actions: list = []

    for row, hero in state.roll.heros_per_row.items():
        if row == APOLLO_ROW or not hero or row in banned:
            continue
        current = state.roll.bids.get(row) or {}
        # w 2p wolno przebić własną ofertę (instrukcja str. 6) — wtedy wypchnięty
        # znacznik trafia do innego boga jak przy zwykłym przebiciu
        # budżet: złoto minus koszt pozostałych ofiar tego gracza
        budget = player.coins - _committed_cost(state, player_id, except_row=row)
        if budget < 1:
            continue
        max_amount = budget + player.priests        # koszt = amount - priests (min 1)
        start = current.get("bid", 0) + 1 if current else 1
        for amount in range(start, max_amount + 1):
            actions.append(RollBid(player=player_id, row=row, amount=amount))

    # Apollo: darmowy; w 2p drugi znacznik do innego boga — chyba że nie ma wyjścia
    if APOLLO_ROW not in mine or not actions:
        actions.append(ApollonBid(player=player_id))
    return actions


# ---------------------------------------------------------------------------
# Aplikacja akcji
# ---------------------------------------------------------------------------

def apply_roll_bid(state: GameState, action: RollBid) -> GameState:
    """Złóż ofiarę. Przebity gracz natychmiast licytuje u innego boga."""
    s = copy.deepcopy(state)
    row, player_id = action.row, action.player
    outbid = (s.roll.bids.get(row) or {}).get("player")

    s.roll.bids[row] = {"player": player_id, "bid": action.amount}
    s.roll.banned.pop(player_id, None)

    if outbid is not None:
        # przelicytowany wraca na początek kolejki i nie może wrócić do tego boga
        s.roll.bid_order = [outbid] + s.roll.bid_order
        s.roll.banned[outbid] = [row]

    return _advance_roll_player(s)


def apply_apollon_bid(state: GameState, action: ApollonBid) -> GameState:
    """Dołącz gracza do rzędu Apollona (kolejne miejsca: 1, 2, ...)."""
    s = copy.deepcopy(state)
    s.roll.bids.setdefault(APOLLO_ROW, []).append(action.player)
    s.roll.banned.pop(action.player, None)
    return _advance_roll_player(s)


def _advance_roll_player(state: GameState) -> GameState:
    """Przesuń na kolejny znacznik; jeśli wszystkie złożone — zakończ ROLL."""
    if state.roll.bid_order:
        state.act_player = state.roll.bid_order[0]
        state.roll.bid_order = state.roll.bid_order[1:]
    else:
        state = finalize_roll(state)
    return state


# ---------------------------------------------------------------------------
# Inicjalizacja fazy ROLL
# ---------------------------------------------------------------------------

def setup_roll_phase(state: GameState, rng: Rng) -> GameState:
    """Przygotuj licytację: rozłóż bogów i ustal kolejność znaczników.

    Kolejność: gracz, który w poprzednim cyklu wykonywał akcje jako ostatni,
    składa ofiarę pierwszy (instrukcja str. 3) — czyli odwrócona `state.acted`.
    W pierwszym cyklu kolejność jest losowa.
    """
    s = copy.deepcopy(state)

    num_rows = visible_gods(s.num_of_players)
    available = [h for h in HEROES_BIDDABLE if h not in s.roll.left_heros]
    rng.shuffle(available)
    left_heroes = s.roll.left_heros[:]

    # bogowie niedostępni w poprzednim cyklu wchodzą jako pierwsi
    heroes_this_round = left_heroes + available[:num_rows - len(left_heroes)]
    rng.shuffle(heroes_this_round)
    placed = heroes_this_round[:num_rows]

    # left_heros liczymy z FAKTYCZNIE wystawionych bogów (patrz test_regressions)
    s.roll.left_heros = [h for h in HEROES_BIDDABLE if h not in placed]

    heros_per_row = {}
    for i, row in enumerate([f"row_{j}" for j in range(1, 5)]):
        heros_per_row[row] = placed[i] if i < num_rows else ""
    heros_per_row[APOLLO_ROW] = "apollon"
    s.roll.heros_per_row = heros_per_row

    if s.acted:
        order = list(reversed(s.acted))
    else:
        players = list(s.players.keys())
        rng.shuffle(players)
        order = players * markers_per_player(s)
    s.acted = []
    s.act_player = order[0]
    s.roll.bid_order = order[1:]

    s.roll.bids = {f"row_{i}": {} for i in range(1, 5)}
    s.roll.bids[APOLLO_ROW] = []
    s.roll.banned = {}

    s.stage = Stage.ROLL
    return s


# ---------------------------------------------------------------------------
# Zakończenie ROLL — rozstrzygnięcie
# ---------------------------------------------------------------------------

def finalize_roll(state: GameState) -> GameState:
    """Rozstrzygnij aukcję: zapłać ofiary, ustal kolejność tur w BOARD.

    Bogowie działają w kolejności rzędów (row_1 pierwszy), Apollo na końcu.
    """
    s = copy.deepcopy(state)
    play_order: list[str] = []
    play_heroes: list[str] = []
    round_heroes: dict[str, list[str]] = {pid: [] for pid in s.players}

    for row in sorted(k for k in s.roll.bids if k != APOLLO_ROW):
        bid = s.roll.bids[row]
        if not bid:
            continue
        player_id, hero = bid["player"], s.roll.heros_per_row[row]
        cost = _bid_cost(bid["bid"], s.players[player_id])
        s.players[player_id].coins = max(0, s.players[player_id].coins - cost)
        play_order.append(player_id)
        play_heroes.append(hero)
        round_heroes[player_id].append(hero)

    for i, player_id in enumerate(s.roll.bids.get(APOLLO_ROW, [])):
        hero = "apollon" if i == 0 else "ap_s"
        play_order.append(player_id)
        play_heroes.append(hero)
        round_heroes[player_id].append(hero)

    s.play_order = play_order
    s.play_heroes = play_heroes
    s.round_heroes = round_heroes
    s.hero_players = {pid: (h[0] if h else "None") for pid, h in round_heroes.items()}
    s.act_player = None
    s.stage = Stage.BOARD
    return s
