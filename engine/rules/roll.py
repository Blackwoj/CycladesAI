"""Reguły fazy ROLL — aukcja herosów.

Port logiki z game/managers/RollManager.py, bez pygame i bez DataCache.
Wszystkie funkcje są czyste (state in → state' out) — wejście nigdy nie jest mutowane.
"""
from __future__ import annotations

import copy

from ..actions import ApollonBid, RollBid
from ..rng import Rng
from ..state import GameState, Player, RollState, Stage

HEROES_BIDDABLE = ["ares", "atena", "posejdon", "zeus"]


# ---------------------------------------------------------------------------
# Pomocnicze
# ---------------------------------------------------------------------------

def _player_total_bid_power(player: Player) -> int:
    """Ile łącznie może wydać gracz (monety + kapłani jako zniżka)."""
    return player.coins + player.priests


def _bid_cost(bid_amount: int, player: Player) -> int:
    """Rzeczywisty koszt złożonej oferty (kapłani są zniżką, min 1 moneta)."""
    cost = bid_amount - player.priests
    return max(cost, 1)


# ---------------------------------------------------------------------------
# Legalne akcje
# ---------------------------------------------------------------------------

def legal_roll_actions(state: GameState) -> list:
    """Legalne akcje dla act_player w fazie ROLL."""
    player_id = state.act_player
    if player_id is None:
        return []
    player = state.players[player_id]
    total_power = _player_total_bid_power(player)
    actions = []

    for row, hero in state.roll.heros_per_row.items():
        if row == "row_5":
            # Apollon — każdy gracz bez herosa bierze tu domyślnie.
            # Akceptujemy ApollonBid tylko jeśli gracz nie zlicytował wyżej.
            already_in = player_id in state.roll.bids.get("row_5", [])
            if not already_in:
                actions.append(ApollonBid(player=player_id))
            continue

        if not hero:  # rząd nieaktywny (mniej niż 4 herosów przy mniejszej liczbie graczy)
            continue

        current_bid = state.roll.bids.get(row, {})
        if current_bid:
            current_bid_value = current_bid.get("bid", 0)
            current_owner = current_bid.get("player")
            # Można przelicytować cudzą ofertę wyższą kwotą
            for amount in range(current_bid_value + 1, total_power + 1):
                if current_owner != player_id and amount <= total_power and player.coins >= 1:
                    actions.append(RollBid(player=player_id, row=row, amount=amount))
        else:
            # Rząd pusty — oferta od 1 (minimum 1 moneta)
            for amount in range(1, total_power + 1):
                if player.coins >= 1:
                    actions.append(RollBid(player=player_id, row=row, amount=amount))

    return actions


# ---------------------------------------------------------------------------
# Aplikacja akcji
# ---------------------------------------------------------------------------

def apply_roll_bid(state: GameState, action: RollBid) -> GameState:
    """Zastosuj licytację. Oddaje monety poprzedniemu licytantowi."""
    s = copy.deepcopy(state)
    row = action.row
    player_id = action.player
    amount = action.amount

    current_bid = s.roll.bids.get(row, {})
    if current_bid:
        outbid_player = current_bid.get("player")
        if outbid_player and outbid_player != player_id:
            # Poprzedni licytant nie płaci — jego monet nie trącamy teraz
            pass

    s.roll.bids[row] = {"player": player_id, "bid": amount}

    # Gracz który przelicytował traci kolejkę (wraca do bid_order na koniec)
    # Jeśli był tu ktoś inny, on dostaje kolejne podejście
    outbid_player = current_bid.get("player") if current_bid else None

    # Usuń act_player z bid_order (jego tura minęła)
    s.roll.bid_order = [p for p in s.roll.bid_order if p != player_id]

    if outbid_player and outbid_player != player_id:
        # Przelicytowany wraca na przód kolejki
        s.roll.bid_order = [outbid_player] + s.roll.bid_order

    # Następny gracz
    s = _advance_roll_player(s)
    return s


def apply_apollon_bid(state: GameState, action: ApollonBid) -> GameState:
    """Dołącz gracza do rzędu Apollona."""
    s = copy.deepcopy(state)
    row5 = s.roll.bids.setdefault("row_5", [])
    if action.player not in row5:
        row5.append(action.player)

    s.roll.bid_order = [p for p in s.roll.bid_order if p != action.player]
    s = _advance_roll_player(s)
    return s


def _advance_roll_player(state: GameState) -> GameState:
    """Przesuń na kolejnego gracza; jeśli wszyscy zagłosowali — zakończ ROLL."""
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
    """Przygotuj fazę aukcji na początku rundy: losuj herosów i kolejność graczy."""
    s = copy.deepcopy(state)

    # Wylosuj herosów do rzędów (do num_players - 1 rzędów)
    num_rows = s.num_of_players - 1
    available = [h for h in HEROES_BIDDABLE if h not in s.roll.left_heros]
    rng.shuffle(available)
    left_heroes = s.roll.left_heros[:]

    heroes_this_round = left_heroes + available[:num_rows - len(left_heroes)]
    rng.shuffle(heroes_this_round)

    # Do rzędów wchodzi tylko num_rows pierwszych — reszta czeka na kolejną rundę.
    placed = heroes_this_round[:num_rows]

    # left_heros liczymy z FAKTYCZNIE wystawionych bogów. Wcześniej liczyliśmy je
    # z heroes_this_round, które przy małej liczbie graczy jest dłuższe niż liczba
    # rzędów — bogowie, którzy nigdy nie weszli do licytacji, znikali z puli.
    # Przy 2 graczach dawało to rozkład 6/3/2/1 na 12 rund zamiast równego.
    s.roll.left_heros = [h for h in HEROES_BIDDABLE if h not in placed]

    heros_per_row = {}
    for i, row in enumerate([f"row_{j}" for j in range(1, 5)]):
        if i < num_rows:
            heros_per_row[row] = placed[i]
        else:
            heros_per_row[row] = ""
    heros_per_row["row_5"] = "apollon"
    s.roll.heros_per_row = heros_per_row

    # Ustaw kolejność licytacji
    bid_order = list(s.players.keys())
    rng.shuffle(bid_order)
    s.roll.bid_order = bid_order[1:]      # pierwszy gracz wchodzi od razu
    s.act_player = bid_order[0]

    # Wyczyść stare oferty
    s.roll.bids = {f"row_{i}": {} for i in range(1, 5)}
    s.roll.bids["row_5"] = []

    s.stage = Stage.ROLL
    return s


# ---------------------------------------------------------------------------
# Zakończenie ROLL — rozstrzygnięcie
# ---------------------------------------------------------------------------

def finalize_roll(state: GameState) -> GameState:
    """Rozstrzygnij aukcję: przypisz herosów, oblicz koszty, ustaw kolejność BOARD."""
    s = copy.deepcopy(state)
    play_order: list[str] = []
    hero_players: dict[str, str] = {pid: "None" for pid in s.players}

    for row, bid in s.roll.bids.items():
        if row == "row_5":
            # Apollon: wszyscy którzy się zapisali
            for i, player_id in enumerate(bid):
                play_order.append(player_id)
                hero_players[player_id] = "apollon" if i == 0 else "ap_s"
        else:
            if not bid:
                continue
            player_id = bid["player"]
            amount = bid["bid"]
            hero = s.roll.heros_per_row[row]

            cost = _bid_cost(amount, s.players[player_id])
            s.players[player_id].coins = max(0, s.players[player_id].coins - cost)
            play_order.append(player_id)
            hero_players[player_id] = hero

    s.play_order = play_order
    s.hero_players = hero_players
    s.act_player = None
    s.stage = Stage.BOARD
    return s
