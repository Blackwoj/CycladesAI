"""GameState — kompletny, jawny stan gry.

Zastępuje globalny game/DataCache.py. Kluczowe własności:
- clone(): głęboka, niezależna kopia (potrzebne dla symulacji MCTS i batcha),
- to_dict()/from_dict(): serializacja JSON (logowanie przebiegów, reprodukcja, FastAPI).
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field as dc_field

from .enums import Stage
from .field import Field
from .player import Player


@dataclass
class GameOptions:
    """Warianty zasad. Siedzą w stanie, żeby klony (MCTS) grały tym samym wariantem."""
    combat_dice: bool = False     # bitwy z kośćmi (oryginał) vs deterministyczne
    creatures: bool = True        # moduł Mitologicznych Stworów
    metros_to_win: int = 2        # 3 w grze dwuosobowej (instrukcja, str. 6)

    def to_dict(self) -> dict:
        return {"combat_dice": self.combat_dice, "creatures": self.creatures,
                "metros_to_win": self.metros_to_win}

    @classmethod
    def from_dict(cls, d: dict) -> "GameOptions":
        return cls(combat_dice=d.get("combat_dice", False), creatures=d.get("creatures", True),
                   metros_to_win=d.get("metros_to_win", 2))


@dataclass
class RollState:
    """Stan etapu aukcji (parytet z RollCacheSection)."""
    # kolejka znaczników ofiarowania (w grze 2-osobowej gracz występuje 2 razy)
    bid_order: list[str] = dc_field(default_factory=list)
    # row_name -> {"player": str, "bid": int}; "row_5" (Apollon) -> list[str]
    bids: dict[str, object] = dc_field(default_factory=dict)
    heros_per_row: dict[str, str] = dc_field(default_factory=dict)
    left_heros: list[str] = dc_field(default_factory=list)
    # gracz -> rzędy, na które nie może teraz licytować (przelicytowany musi wybrać INNEGO boga)
    banned: dict[str, list[str]] = dc_field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "bid_order": list(self.bid_order),
            "bids": copy.deepcopy(self.bids),
            "heros_per_row": dict(self.heros_per_row),
            "left_heros": list(self.left_heros),
            "banned": {p: list(r) for p, r in self.banned.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RollState":
        return cls(
            bid_order=list(d.get("bid_order", [])),
            bids=copy.deepcopy(d.get("bids", {})),
            heros_per_row=dict(d.get("heros_per_row", {})),
            left_heros=list(d.get("left_heros", [])),
            banned={p: list(r) for p, r in d.get("banned", {}).items()},
        )


@dataclass
class CardState:
    """Mitologiczne Stwory (engine/rules/creatures.py).

    track[0..2] = pola toru o koszcie 4 / 3 / 2 GP. Figurki (Kraken, Minotaur,
    Chiron, Meduza, Polifem) działają trwale, więc trzymamy je osobno.
    """
    hands: dict[str, list[str]] = dc_field(default_factory=dict)   # nieużywane (zgodność)
    market: list[str] = dc_field(default_factory=list)             # nieużywane (zgodność)
    deck: list[str] = dc_field(default_factory=list)
    discard: list[str] = dc_field(default_factory=list)
    track: list[str | None] = dc_field(default_factory=lambda: [None, None, None])
    # figurka -> {"field": id, "owner": gracz}
    figures: dict[str, dict] = dc_field(default_factory=dict)
    # gracz -> ile zniżek ze Świątyń/Metropolii zużył w tym cyklu
    temple_uses: dict[str, int] = dc_field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "hands": {p: list(c) for p, c in self.hands.items()},
            "market": list(self.market),
            "deck": list(self.deck),
            "discard": list(self.discard),
            "track": list(self.track),
            "figures": copy.deepcopy(self.figures),
            "temple_uses": dict(self.temple_uses),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CardState":
        return cls(
            hands={p: list(c) for p, c in d.get("hands", {}).items()},
            market=list(d.get("market", [])),
            deck=list(d.get("deck", [])),
            discard=list(d.get("discard", [])),
            track=list(d.get("track", [None, None, None])),
            figures=copy.deepcopy(d.get("figures", {})),
            temple_uses=dict(d.get("temple_uses", {})),
        )


@dataclass
class BoardPhaseState:
    """Ulotny stan fazy BOARD — resetuje się na początku każdej tury gracza."""
    entity_price: int = 0         # ile jednostek zrekrutowano w tej turze (indeks cennika)
    poseidon_jumps: int = 0       # nieużywane — ruch floty to teraz 1 GP za do 3 pól
    metro_by_philo: bool = False  # metropolia przez 4 filozofów (Atena)
    metro_by_build: bool = False  # metropolia przez 1 budynek każdego herosa
    zeus_card: bool = False       # karta Zeusa dostępna w tej turze
    athena_card: bool = False     # karta Ateny dostępna w tej turze
    apollon_income: bool = False  # Apollon może jeszcze położyć znacznik dochodu
    # wybór w toku — dopóki nie jest rozstrzygnięty, legal_actions to tylko jego opcje
    # {"kind": "metropolis", "source": ...} | {"kind": "creature", "card": ..., ...}
    pending: dict | None = None

    def to_dict(self) -> dict:
        return {
            "entity_price": self.entity_price,
            "poseidon_jumps": self.poseidon_jumps,
            "metro_by_philo": self.metro_by_philo,
            "metro_by_build": self.metro_by_build,
            "zeus_card": self.zeus_card,
            "athena_card": self.athena_card,
            "apollon_income": self.apollon_income,
            "pending": copy.deepcopy(self.pending),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BoardPhaseState":
        return cls(
            entity_price=d.get("entity_price", 0),
            poseidon_jumps=d.get("poseidon_jumps", 0),
            metro_by_philo=d.get("metro_by_philo", False),
            metro_by_build=d.get("metro_by_build", False),
            zeus_card=d.get("zeus_card", False),
            athena_card=d.get("athena_card", False),
            apollon_income=d.get("apollon_income", False),
            pending=copy.deepcopy(d.get("pending")),
        )


@dataclass
class GameState:
    num_of_players: int = 0
    stage: Stage = Stage.SETUP
    round_no: int = 0

    act_player: str | None = None
    act_hero: str | None = None

    play_order: list[str] = dc_field(default_factory=list)
    # bóg każdej pozostałej tury (równoległe do play_order); w grze 2-osobowej
    # gracz ma dwie tury z różnymi bogami, więc hero_players nie wystarcza
    play_heroes: list[str] = dc_field(default_factory=list)
    hero_players: dict[str, str] = dc_field(default_factory=dict)   # player -> hero w tej rundzie
    round_heroes: dict[str, list[str]] = dc_field(default_factory=dict)  # player -> bogowie w tej rundzie
    # kolejność akcji w tej rundzie (do ustalenia kolejności licytacji w następnej)
    acted: list[str] = dc_field(default_factory=list)
    winners: list[str] = dc_field(default_factory=list)
    options: GameOptions = dc_field(default_factory=GameOptions)

    players: dict[str, Player] = dc_field(default_factory=dict)
    fields: dict[str, Field] = dc_field(default_factory=dict)

    roll: RollState = dc_field(default_factory=RollState)
    board: BoardPhaseState = dc_field(default_factory=BoardPhaseState)
    cards: CardState = dc_field(default_factory=CardState)

    def clone(self) -> "GameState":
        """Głęboka, w pełni niezależna kopia."""
        return copy.deepcopy(self)

    def to_dict(self) -> dict:
        return {
            "num_of_players": self.num_of_players,
            "stage": self.stage.value,
            "round_no": self.round_no,
            "act_player": self.act_player,
            "act_hero": self.act_hero,
            "play_order": list(self.play_order),
            "play_heroes": list(self.play_heroes),
            "hero_players": dict(self.hero_players),
            "round_heroes": {p: list(h) for p, h in self.round_heroes.items()},
            "acted": list(self.acted),
            "winners": list(self.winners),
            "options": self.options.to_dict(),
            "players": {pid: p.to_dict() for pid, p in self.players.items()},
            "fields": {fid: f.to_dict() for fid, f in self.fields.items()},
            "roll": self.roll.to_dict(),
            "board": self.board.to_dict(),
            "cards": self.cards.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GameState":
        return cls(
            num_of_players=d.get("num_of_players", 0),
            stage=Stage(d.get("stage", "setup")),
            round_no=d.get("round_no", 0),
            act_player=d.get("act_player"),
            act_hero=d.get("act_hero"),
            play_order=list(d.get("play_order", [])),
            play_heroes=list(d.get("play_heroes", [])),
            hero_players=dict(d.get("hero_players", {})),
            round_heroes={p: list(h) for p, h in d.get("round_heroes", {}).items()},
            acted=list(d.get("acted", [])),
            winners=list(d.get("winners", [])),
            options=GameOptions.from_dict(d.get("options", {})),
            players={pid: Player.from_dict(p) for pid, p in d.get("players", {}).items()},
            fields={fid: Field.from_dict(f) for fid, f in d.get("fields", {}).items()},
            roll=RollState.from_dict(d.get("roll", {})),
            board=BoardPhaseState.from_dict(d.get("board", {})),
            cards=CardState.from_dict(d.get("cards", {})),
        )
