"""Testy regresyjne — pilnują błędów wykrytych po Fazie 6.

Każdy test odpowiada jednemu konkretnemu błędowi; opis w docstringu mówi, co
było zepsute, żeby przy przyszłym refaktorze było jasne, czego nie wolno cofnąć.
"""
from engine.actions import MoveEntity, PlaceEntity
from engine.agents import RandomAgent
from engine.engine import GameEngine
from engine.rng import Rng
from engine.rules.board import (
    _apply_move_entity,
    legal_board_actions,
    start_player_turn,
)
from engine.rules.setup import build_initial_state
from engine.state import (
    Entity,
    Field,
    FieldType,
    GameState,
    Player,
    Stage,
)


def _two_water_state(ships=2, coins=5):
    """Minimalny stan: dwa sąsiadujące pola wodne, statki gracza na W1."""
    return GameState(
        num_of_players=2, stage=Stage.BOARD, act_player="p1", act_hero="posejdon",
        players={"p1": Player("p1", coins=coins), "p2": Player("p2", coins=coins)},
        fields={
            "W1": Field(type=FieldType.WATER, owner="p1",
                        entity=Entity(kind="ship", quantity=ships),
                        neighbors=["W2"]),
            "W2": Field(type=FieldType.WATER, owner=None,
                        entity=Entity(), neighbors=["W1", "W3"]),
            "W3": Field(type=FieldType.WATER, owner=None,
                        entity=Entity(), neighbors=["W2"]),
        },
    )


def _board_state(n=2, seed=1, hero="ares"):
    """Stan w fazie BOARD z wymuszonym herosem aktywnego gracza."""
    s = build_initial_state(n, Rng(seed))
    s.stage = Stage.BOARD
    players = list(s.players)
    s.hero_players = {players[0]: hero, players[1]: "posejdon"}
    s.play_order = list(players)
    s = start_player_turn(s)
    s.act_hero = hero
    return s


# ---------------------------------------------------------------------------
# 1. Gubienie entity.kind przy opróżnieniu pola źródłowego
# ---------------------------------------------------------------------------

def test_move_all_ships_preserves_kind():
    """Ruch WSZYSTKICH statkow z pola nie może gubić kind.

    Błąd: entity_kind czytano z from_f.entity PO wyzerowaniu pola, więc pole
    docelowe dostawało kind=None i statki przestawały być statkami.
    """
    s = _two_water_state(ships=2)
    s2, info = _apply_move_entity(
        s, MoveEntity(player="p1", from_field="W1", to_field="W2", quantity=2), Rng(1))
    assert info["valid"]
    assert s2.fields["W2"].entity.kind == "ship"
    assert s2.fields["W2"].entity.quantity == 2


def test_move_partial_ships_preserves_kind():
    """Wariant kontrolny: ruch części statków zawsze działał — musi dalej działać."""
    s = _two_water_state(ships=2)
    s2, _ = _apply_move_entity(
        s, MoveEntity(player="p1", from_field="W1", to_field="W2", quantity=1), Rng(1))
    assert s2.fields["W1"].entity.kind == "ship"
    assert s2.fields["W2"].entity.kind == "ship"


def test_ship_stays_a_ship_across_two_moves_without_coins():
    """Statek po przeskoku na puste pole nadal jest statkiem w NASTĘPNYM ruchu.

    Pełny łańcuch błędu — pojedynczy ruch nie wystarcza, żeby go wykryć:
    ruch 1 opróżnia W1, więc pole W2 dostawało kind=None; ruch 2 z W2 szedł
    wtedy ścieżką kosztu wojownika i przy coins=0 był odrzucany jako
    "brak monet na ruch wojownika", mimo że legal_posejdon_actions() go
    dopuszczało (brama: coins>=1 OR poseidon_jumps>0).
    """
    s = _two_water_state(ships=2, coins=1)
    # Ruch 1: wszystkie statki z W1 na W2 — pole źródłowe pustoszeje.
    s, info1 = _apply_move_entity(
        s, MoveEntity(player="p1", from_field="W1", to_field="W2", quantity=2), Rng(1))
    assert info1["valid"], info1
    assert s.players["p1"].coins == 0, "ruch 1 miał kosztować 1 monetę"
    assert s.board.poseidon_jumps == 2, "ruch 1 miał odblokować 2 darmowe przejścia"

    # Ruch 2: bez monet, ale z darmowym przejściem Posejdona.
    s, info2 = _apply_move_entity(
        s, MoveEntity(player="p1", from_field="W2", to_field="W3", quantity=2), Rng(1))
    assert info2["valid"], info2
    assert s.fields["W3"].entity.kind == "ship"
    assert s.board.poseidon_jumps == 1


# ---------------------------------------------------------------------------
# 2. Wojownicy na otwartym morzu
# ---------------------------------------------------------------------------

def test_warriors_cannot_move_onto_water():
    """Ares nie może przesunąć wojowników na pole wodne.

    Błąd: generator iterował po wszystkich polach, a can_warrior_reach()
    dopuszczał dowolne pole sąsiednie — wojownicy lądowali na otwartym morzu
    (do 16 pól wodnych na partię), gdzie Posejdon proponował im "ruch statku".
    Ścieżka DFS przez własną wodę (most ze statków) pozostaje dozwolona.
    """
    s = _board_state(hero="ares")
    s.players[s.act_player].coins = 20
    moves = [a for a in legal_board_actions(s) if isinstance(a, MoveEntity)]
    assert moves, "brak ruchów wojowników do sprawdzenia"
    for m in moves:
        assert s.fields[m.to_field].type == FieldType.ISLAND, \
            f"ruch wojownika na wodę: {m.to_dict()}"


def test_poseidon_ignores_warriors_standing_on_water():
    """Generator Posejdona pomija pola wodne, na których nie stoją statki."""
    s = _two_water_state(ships=1)
    s.fields["W1"].entity = Entity(kind="warrior", quantity=1)
    moves = [a for a in legal_board_actions(s) if isinstance(a, MoveEntity)]
    assert not [m for m in moves if m.from_field == "W1"]


# ---------------------------------------------------------------------------
# 3. Reprodukowalność — kolejność legal_actions nie może zależeć od hashów
# ---------------------------------------------------------------------------

def test_ship_placements_are_deterministically_ordered():
    """Akcje rekrutacji statków muszą wychodzić w porządku sortowanym.

    Błąd: generator iterował po zbiorze (set) pól wodnych, więc kolejność
    legal_actions() zależała od PYTHONHASHSEED. Ten sam seed w dwóch procesach
    dawał różne przebiegi gry, co przewracało reprodukowalność eksperymentów.
    """
    s = _board_state(hero="posejdon")
    s.act_hero = "posejdon"
    s.hero_players[s.act_player] = "posejdon"
    s.players[s.act_player].coins = 20
    ships = [a.field_id for a in legal_board_actions(s)
             if isinstance(a, PlaceEntity) and a.kind == "ship"]
    assert ships, "brak akcji rekrutacji statków do sprawdzenia"
    assert ships == sorted(ships)


# ---------------------------------------------------------------------------
# 4. Gracze-widma przy mniejszej liczbie graczy
# ---------------------------------------------------------------------------

def test_no_phantom_owners_for_fewer_players():
    """Rozstawienie startowe nie może zawierać graczy poza state.players.

    Błąd: pliki JSON opisują rozstawienie dla 5 graczy i wczytywano je w
    całości — przy 2 graczach 15 z 22 zajętych pól należało do p3/p4/p5,
    którzy nie mieli agenta i nigdy się nie ruszali.
    """
    for n in (2, 3, 4, 5):
        s = build_initial_state(n, Rng(42))
        owners = {f.owner for f in s.fields.values() if f.owner}
        assert owners <= set(s.players), \
            f"n={n}: pola bez właściciela w grze: {owners - set(s.players)}"


def test_fewer_players_leaves_islands_neutral():
    """Pozycje nieużywanych graczy stają się neutralne, nie znikają z planszy."""
    s2 = build_initial_state(2, Rng(42))
    s5 = build_initial_state(5, Rng(42))
    assert set(s2.fields) == set(s5.fields), "liczba graczy nie zmienia layoutu pól"
    neutral2 = sum(1 for f in s2.fields.values()
                   if f.type == FieldType.ISLAND and f.owner is None)
    neutral5 = sum(1 for f in s5.fields.values()
                   if f.type == FieldType.ISLAND and f.owner is None)
    assert neutral2 > neutral5


# ---------------------------------------------------------------------------
# 5. Test integracyjny — legal_actions() i step() muszą się zgadzać
# ---------------------------------------------------------------------------

def test_engine_never_rejects_its_own_legal_action():
    """Żadna akcja z legal_actions() nie może zostać odrzucona przez step().

    To niezmiennik całego silnika: agent wybierający wyłącznie z legal_actions
    nie powinien generować ani jednego nielegalnego ruchu. Metryka
    illegal_count z ExperimentRunner służy do oceny agentów LLM, więc szum
    pochodzący z samego silnika czyni ją bezwartościową.
    """
    master = Rng(1234)
    rejected = []
    for _ in range(3):
        rng = master.spawn()
        engine = GameEngine(rng=rng)
        state = engine.new_game(num_players=2, rng=rng.spawn())
        agents = {pid: RandomAgent(Rng(100 + i))
                  for i, pid in enumerate(state.players)}
        steps = 0
        while not engine.is_terminal(state) and steps < 200:
            if state.act_player is None:
                break
            legal = engine.legal_actions(state)
            if not legal:
                break
            view = engine.state_view(state, state.act_player)
            action = agents[state.act_player].choose(view, legal)
            state, info = engine.step(state, action)
            if not info.get("valid", True):
                rejected.append((action.to_dict(), info))
            steps += 1
    assert not rejected, f"step() odrzucił {len(rejected)} własnych legalnych akcji: {rejected[:3]}"
