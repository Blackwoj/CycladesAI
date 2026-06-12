"""Reguły fazy BOARD — tury graczy.

Port logiki z game/managers/BoardManager.py i sub-managerów (Warrior, Ship,
Buildings, PrepareStageManager.define_player_hero), bez pygame i DataCache.
Wszystkie funkcje czyste: (state, action) → state'.
"""
from __future__ import annotations

import copy

from ..actions import Action, Build, BuyCard, EndTurn, MoveEntity, PlaceEntity, PlayCard
from ..rng import Rng
from ..state import Building, BoardPhaseState, Entity, Field, FieldType, GameState, Stage
from .graph import BoardGraph
from .setup import (
    WARRIOR_PRICING, SHIP_PRICING,
    load_board_data,
)

_MAX_WARRIORS = 6
_MAX_SHIPS = 6
_ATENA_PHILO_FOR_METRO = 4    # 4 filozofów → prawo do metropolii
_BUILD_COST = 2


# ---------------------------------------------------------------------------
# Graf — budowany raz z danych JSON lub przekazywany z zewnątrz
# ---------------------------------------------------------------------------

def _build_graph(fields: dict) -> BoardGraph:
    g = BoardGraph()
    for fid, field in fields.items():
        g.add_vertex(fid, field.owner)
    for fid, field in fields.items():
        for nb in field.neighbors:
            if nb in fields:
                g.add_edge(fid, nb)
    g.sync_owners(fields)
    return g


# ---------------------------------------------------------------------------
# Przejście do tury konkretnego gracza
# ---------------------------------------------------------------------------

def start_player_turn(state: GameState) -> GameState:
    """Pobierz następnego gracza z play_order i zainicjalizuj jego turę."""
    s = copy.deepcopy(state)
    if not s.play_order:
        return s   # faza BOARD skończona — wywoła end_board_phase
    s.act_player = s.play_order[0]
    s.play_order = s.play_order[1:]
    s.act_hero = s.hero_players.get(s.act_player, "None")

    # Reset ulotnych pól tury
    s.board = BoardPhaseState(entity_price=0, poseidon_jumps=0)

    # Natychmiastowe efekty herosa — Atena i Zeus dają karty, Apollon daje monety
    hero = s.act_hero
    if hero == "atena":
        s.players[s.act_player].philosophers += 1
        s.board.athena_card = True
        s = _check_atena_metro(s)
    elif hero == "zeus":
        s.players[s.act_player].priests += 1
        s.board.zeus_card = True
    elif hero in ("apollon", "ap_s"):
        owned_islands = sum(
            1 for f in s.fields.values()
            if f.type == FieldType.ISLAND and f.owner == s.act_player
        )
        s.players[s.act_player].coins += 1 if owned_islands > 1 else 4

    return s


def _check_atena_metro(state: GameState) -> GameState:
    """Jeśli gracz ma >= 4 filozofów → zezwól na budowę metropolii."""
    player = state.players[state.act_player]
    if player.philosophers >= _ATENA_PHILO_FOR_METRO:
        player.philosophers -= _ATENA_PHILO_FOR_METRO
        state.board.metro_by_philo = True
    return state


# ---------------------------------------------------------------------------
# Legalne akcje — BOARD
# ---------------------------------------------------------------------------

def legal_board_actions(state: GameState) -> list[Action]:
    """Legalne akcje dla act_player w fazie BOARD zależne od herosa."""
    hero = state.act_hero
    player_id = state.act_player
    if player_id is None or hero is None:
        return []

    actions: list[Action] = []

    if hero == "ares":
        actions += _legal_ares_actions(state)
    elif hero == "posejdon":
        actions += _legal_posejdon_actions(state)
    elif hero == "atena":
        actions += _legal_atena_actions(state)
    elif hero == "zeus":
        actions += _legal_zeus_actions(state)
    elif hero in ("apollon", "ap_s"):
        # Apollon nie ma akcji bojowych — tylko build i end
        actions += _legal_build_actions(state)

    # PlayCard — o ile rejestr kart nie jest pusty (szew Fazy 7)
    # (brak akcji gdy rejestr pusty)

    # Zawsze można zakończyć turę
    actions.append(EndTurn(player=player_id))
    return actions


def _count_entities(state: GameState, player: str, kind: str) -> int:
    field_type = FieldType.ISLAND if kind == "warrior" else FieldType.WATER
    return sum(
        f.entity.quantity
        for f in state.fields.values()
        if f.type == field_type and f.owner == player and f.entity.quantity > 0
    )


def _legal_ares_actions(state: GameState) -> list[Action]:
    """Ares: rekrut wojowników, przesuwanie, budowanie."""
    player_id = state.act_player
    player = state.players[player_id]
    actions: list[Action] = []
    g = _build_graph(state.fields)
    g.sync_owners(state.fields)

    entity_price = state.board.entity_price
    price_idx = min(entity_price, len(WARRIOR_PRICING) - 1)
    recruit_cost = WARRIOR_PRICING[price_idx]
    total_warriors = _count_entities(state, player_id, "warrior")

    # Rekrut
    if player.coins >= recruit_cost and total_warriors < _MAX_WARRIORS:
        for fid, field in state.fields.items():
            if field.type == FieldType.ISLAND and field.owner == player_id:
                actions.append(PlaceEntity(player=player_id, field_id=fid, kind="warrior", quantity=1))

    # Ruch wojowników
    if player.coins >= 1:
        for from_id, from_field in state.fields.items():
            if (from_field.type == FieldType.ISLAND
                    and from_field.owner == player_id
                    and from_field.entity.quantity > 0):
                for to_id in state.fields:
                    if to_id == from_id:
                        continue
                    if g.can_warrior_reach(from_id, to_id, player_id):
                        for qty in range(1, from_field.entity.quantity + 1):
                            actions.append(MoveEntity(
                                player=player_id, from_field=from_id,
                                to_field=to_id, quantity=qty,
                            ))

    # Budowanie
    actions += _legal_build_actions(state)
    return actions


def _legal_posejdon_actions(state: GameState) -> list[Action]:
    """Posejdon: rekrut statków, przesuwanie, budowanie."""
    player_id = state.act_player
    player = state.players[player_id]
    actions: list[Action] = []

    price_idx = min(state.board.entity_price, len(SHIP_PRICING) - 1)
    recruit_cost = SHIP_PRICING[price_idx]
    total_ships = _count_entities(state, player_id, "ship")

    # Rekrut statku — na polu wodnym sąsiadującym z wyspą gracza
    if player.coins >= recruit_cost and total_ships < _MAX_SHIPS:
        owned_islands = {fid for fid, f in state.fields.items()
                         if f.type == FieldType.ISLAND and f.owner == player_id}
        valid_water = {
            nb for iid in owned_islands
            for nb in state.fields[iid].neighbors
            if nb in state.fields and state.fields[nb].type == FieldType.WATER
        }
        for fid in valid_water:
            actions.append(PlaceEntity(player=player_id, field_id=fid, kind="ship", quantity=1))

    # Ruch statków — jeden krok między sąsiednimi polami wodnymi
    if player.coins >= 1 or state.board.poseidon_jumps > 0:
        for from_id, from_field in state.fields.items():
            if (from_field.type == FieldType.WATER
                    and from_field.owner == player_id
                    and from_field.entity.quantity > 0):
                for to_id in from_field.neighbors:
                    if to_id in state.fields and state.fields[to_id].type == FieldType.WATER:
                        for qty in range(1, from_field.entity.quantity + 1):
                            actions.append(MoveEntity(
                                player=player_id, from_field=from_id,
                                to_field=to_id, quantity=qty,
                            ))

    actions += _legal_build_actions(state)
    return actions


def _legal_atena_actions(state: GameState) -> list[Action]:
    """Atena: kup kartę filozofa (koszt 4 monety), buduj, zbuduj metropolię jeśli warunki."""
    player_id = state.act_player
    player = state.players[player_id]
    actions: list[Action] = []

    if player.coins >= 4 and state.board.athena_card:
        actions.append(BuyCard(player=player_id, hero="atena"))

    if state.board.metro_by_philo:
        actions += _legal_metro_actions(state)

    actions += _legal_build_actions(state)
    return actions


def _legal_zeus_actions(state: GameState) -> list[Action]:
    """Zeus: kup kartę kapłana (koszt 4 monety), buduj."""
    player_id = state.act_player
    player = state.players[player_id]
    actions: list[Action] = []

    if player.coins >= 4 and state.board.zeus_card:
        actions.append(BuyCard(player=player_id, hero="zeus"))

    actions += _legal_build_actions(state)
    return actions


def _legal_build_actions(state: GameState) -> list[Build]:
    """Budowania — wspólne dla wszystkich herosów (koszt 2 monety)."""
    player_id = state.act_player
    player = state.players[player_id]
    if player.coins < _BUILD_COST:
        return []
    hero = state.act_hero
    if hero in ("apollon", "ap_s", "atena", "zeus"):
        # Tylko Ares i Posejdon stawiają budynki fizyczne na planszy;
        # Atena/Zeus kupują karty a nie budynki — pomijamy tu.
        # Apollon buduje przez osobną ścieżkę (dochód) — tu też skip.
        return []

    actions = []
    for fid, field in state.fields.items():
        if field.type != FieldType.ISLAND or field.owner != player_id:
            continue
        if field.is_metropolis:
            continue
        for slot, building in field.buildings.items():
            if building is None and not _slot_is_metro_reserved(state, fid, slot):
                actions.append(Build(player=player_id, field_id=fid, hero=hero))
                break   # jedno Build na wyspę żeby nie multiplikować
    return actions


def _legal_metro_actions(state: GameState) -> list[Build]:
    """Budowanie metropolii (przez filozofów Ateny). Zwraca Build z hero='metro'."""
    player_id = state.act_player
    actions = []
    for fid, field in state.fields.items():
        if (field.type == FieldType.ISLAND
                and field.owner == player_id
                and not field.is_metropolis):
            actions.append(Build(player=player_id, field_id=fid, hero="metro"))
    return actions


def _slot_is_metro_reserved(state: GameState, field_id: str, slot: str) -> bool:
    """Czy slot jest zarezerwowany dla metropolii (miejsca big w konfiguracji)?"""
    # Uproszczenie: nie blokujemy slotów w silniku headless — GUI to robi wizualnie.
    return False


# ---------------------------------------------------------------------------
# Walidacja akcji
# ---------------------------------------------------------------------------

def validate_action(state: GameState, action: Action) -> bool:
    """Sprawdź, czy akcja jest legalna. False → AccjeError bez wyjątku."""
    legal = legal_board_actions(state)
    for la in legal:
        if la == action:
            return True
    # Elastyczna walidacja typów (bez sprawdzania parametrów ilościowych):
    legal_types = {type(a) for a in legal}
    return type(action) in legal_types


# ---------------------------------------------------------------------------
# Aplikacja akcji — BOARD
# ---------------------------------------------------------------------------

def apply_board_action(state: GameState, action: Action, rng: Rng) -> tuple[GameState, dict]:
    """Zastosuj akcję. Zwraca (nowy_stan, info). Nie mutuje wejścia."""
    if isinstance(action, PlaceEntity):
        return _apply_place_entity(state, action)
    if isinstance(action, MoveEntity):
        return _apply_move_entity(state, action, rng)
    if isinstance(action, Build):
        return _apply_build(state, action)
    if isinstance(action, BuyCard):
        return _apply_buy_card(state, action)
    if isinstance(action, EndTurn):
        return _apply_end_turn(state)
    if isinstance(action, PlayCard):
        return _apply_play_card(state, action)
    raise ValueError(f"Nieznana akcja: {action}")


def _apply_place_entity(state: GameState, action: PlaceEntity) -> tuple[GameState, dict]:
    s = copy.deepcopy(state)
    player = s.players[action.player]
    field = s.fields[action.field_id]

    price_idx = min(s.board.entity_price, len(WARRIOR_PRICING) - 1)
    cost = WARRIOR_PRICING[price_idx] if action.kind == "warrior" else SHIP_PRICING[price_idx]

    if player.coins < cost:
        return state, {"valid": False, "reason": "brak monet"}
    if _count_entities(s, action.player, action.kind) >= _MAX_WARRIORS:
        return state, {"valid": False, "reason": "max jednostek"}

    player.coins -= cost
    field.entity.quantity += 1
    if not field.entity.kind:
        field.entity.kind = action.kind
    if field.owner is None:
        field.owner = action.player

    s.board.entity_price += 1
    return s, {"valid": True}


def _apply_move_entity(state: GameState, action: MoveEntity, rng: Rng) -> tuple[GameState, dict]:
    s = copy.deepcopy(state)
    player_id = action.player
    from_f = s.fields[action.from_field]
    to_f = s.fields[action.to_field]

    # Koszt ruchu
    if action.kind == "ship" or (from_f.entity.kind == "ship"):
        if s.board.poseidon_jumps > 0:
            s.board.poseidon_jumps -= 1
        else:
            if s.players[player_id].coins < 1:
                return state, {"valid": False, "reason": "brak monet na ruch statku"}
            s.players[player_id].coins -= 1
            s.board.poseidon_jumps = 2  # kolejne 2 przejścia darmowe w tej ramce
    else:
        if s.players[player_id].coins < 1:
            return state, {"valid": False, "reason": "brak monet na ruch wojownika"}
        s.players[player_id].coins -= 1

    qty = action.quantity
    from_f.entity.quantity -= qty

    if from_f.entity.quantity == 0:
        from_f.entity = Entity()
        if from_f.type == FieldType.WATER:
            from_f.owner = None

    entity_kind = action.kind if action.kind else from_f.entity.kind

    if to_f.owner is None or to_f.owner == player_id:
        # Ruch na własne lub neutralne pole
        to_f.entity.quantity += qty
        to_f.entity.kind = entity_kind
        to_f.owner = player_id
        return s, {"valid": True, "combat": False}

    # Walka
    attacker = qty
    defender = to_f.entity.quantity
    diff = attacker - defender

    if diff > 0:
        to_f.entity = Entity(kind=entity_kind, quantity=diff)
        to_f.owner = player_id
        return s, {"valid": True, "combat": True, "winner": player_id}
    elif diff < 0:
        to_f.entity.quantity = abs(diff)
        return s, {"valid": True, "combat": True, "winner": to_f.owner}
    else:
        # Remis: wojownicy — obrońca zostaje; statki — obaj giną
        if entity_kind == "ship":
            to_f.entity = Entity()
            to_f.owner = None
        else:
            # Remis wojownicy — obrońca wygrywa (1 zostaje)
            to_f.entity.quantity = 1
        return s, {"valid": True, "combat": True, "winner": to_f.owner}


def _apply_build(state: GameState, action: Build) -> tuple[GameState, dict]:
    s = copy.deepcopy(state)
    player = s.players[action.player]
    field = s.fields[action.field_id]

    if action.hero == "metro":
        # Budowa metropolii (filozofowie)
        if not s.board.metro_by_philo:
            return state, {"valid": False, "reason": "brak prawa do metropolii"}
        field.is_metropolis = True
        s.board.metro_by_philo = False
        return s, {"valid": True, "metropolis": True}

    if player.coins < _BUILD_COST:
        return state, {"valid": False, "reason": "brak monet"}
    if field.type != FieldType.ISLAND or field.owner != action.player:
        return state, {"valid": False, "reason": "nie twoja wyspa"}

    # Znajdź wolny slot
    for slot, building in field.buildings.items():
        if building is None:
            field.buildings[slot] = Building(hero=action.hero)
            player.coins -= _BUILD_COST
            # Sprawdź czy to otwiera budowę metropolii przez budynki
            s = _check_metro_by_buildings(s, action.player)
            return s, {"valid": True}

    return state, {"valid": False, "reason": "brak wolnego slotu"}


def _check_metro_by_buildings(state: GameState, player_id: str) -> GameState:
    """Jeśli gracz ma budynek każdego herosa → prawo do metropolii."""
    from ..state.enums import HEROES
    required = set(HEROES.BIDDABLE)
    player_buildings: set[str] = set()
    for field in state.fields.values():
        if field.type == FieldType.ISLAND and field.owner == player_id:
            for b in field.buildings.values():
                if b:
                    player_buildings.add(b.hero)
    if required.issubset(player_buildings):
        state.board.metro_by_build = True
    return state


def _apply_buy_card(state: GameState, action: BuyCard) -> tuple[GameState, dict]:
    s = copy.deepcopy(state)
    player = s.players[action.player]
    if player.coins < 4:
        return state, {"valid": False, "reason": "brak 4 monet"}

    player.coins -= 4
    if action.hero == "atena":
        player.philosophers += 1
        s.board.athena_card = False
        s = _check_atena_metro(s)
    elif action.hero == "zeus":
        player.priests += 1
        s.board.zeus_card = False
    return s, {"valid": True}


def _apply_play_card(state: GameState, action: PlayCard) -> tuple[GameState, dict]:
    """SZEW — rejestr kart pusty; CardRegistry podłącza się tu w Fazie 7."""
    return state, {"valid": False, "reason": "brak kart w rejestrze (Faza 7)"}


def _apply_end_turn(state: GameState) -> tuple[GameState, dict]:
    s = copy.deepcopy(state)
    s.act_player = None
    s.act_hero = None
    # Kolejnego gracza uruchomi engine.step po sprawdzeniu play_order
    return s, {"valid": True, "end_turn": True}
