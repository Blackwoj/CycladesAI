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
class RollState:
    """Stan etapu aukcji (parytet z RollCacheSection)."""
    bid_order: list[str] = dc_field(default_factory=list)
    # row_name -> {"player": str, "bid": int}; "row_5" (Apollon) -> list[str]
    bids: dict[str, object] = dc_field(default_factory=dict)
    heros_per_row: dict[str, str] = dc_field(default_factory=dict)
    left_heros: list[str] = dc_field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "bid_order": list(self.bid_order),
            "bids": copy.deepcopy(self.bids),
            "heros_per_row": dict(self.heros_per_row),
            "left_heros": list(self.left_heros),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RollState":
        return cls(
            bid_order=list(d.get("bid_order", [])),
            bids=copy.deepcopy(d.get("bids", {})),
            heros_per_row=dict(d.get("heros_per_row", {})),
            left_heros=list(d.get("left_heros", [])),
        )


@dataclass
class CardState:
    """SZEW pod moduł kart specjalnych (Faza 7).

    Na razie pusty — istnieje, żeby reszta kodu (akcja PlayCard, serializacja,
    projekcja stanu dla LLM) była gotowa, zanim dodamy treść kart.
    """
    hands: dict[str, list[str]] = dc_field(default_factory=dict)   # player -> [card_id]
    market: list[str] = dc_field(default_factory=list)             # dostępne do kupienia

    def to_dict(self) -> dict:
        return {
            "hands": {p: list(c) for p, c in self.hands.items()},
            "market": list(self.market),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CardState":
        return cls(
            hands={p: list(c) for p, c in d.get("hands", {}).items()},
            market=list(d.get("market", [])),
        )


@dataclass
class BoardPhaseState:
    """Ulotny stan fazy BOARD — resetuje się na początku każdej tury gracza."""
    entity_price: int = 0         # koszt kolejnego rekrutowanego wojownika/statku
    poseidon_jumps: int = 0       # pozostałe darmowe przejścia statku (Posejdon)
    metro_by_philo: bool = False  # metropolia przez 4 filozofów (Atena)
    metro_by_build: bool = False  # metropolia przez 1 budynek każdego herosa
    zeus_card: bool = False       # karta Zeusa dostępna w tej turze
    athena_card: bool = False     # karta Ateny dostępna w tej turze
    apollon_income: bool = False  # Apollon może jeszcze położyć znacznik dochodu

    def to_dict(self) -> dict:
        return {
            "entity_price": self.entity_price,
            "poseidon_jumps": self.poseidon_jumps,
            "metro_by_philo": self.metro_by_philo,
            "metro_by_build": self.metro_by_build,
            "zeus_card": self.zeus_card,
            "athena_card": self.athena_card,
            "apollon_income": self.apollon_income,
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
        )


@dataclass
class GameState:
    num_of_players: int = 0
    stage: Stage = Stage.SETUP
    round_no: int = 0

    act_player: str | None = None
    act_hero: str | None = None

    play_order: list[str] = dc_field(default_factory=list)
    hero_players: dict[str, str] = dc_field(default_factory=dict)   # player -> hero w tej rundzie

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
            "hero_players": dict(self.hero_players),
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
            hero_players=dict(d.get("hero_players", {})),
            players={pid: Player.from_dict(p) for pid, p in d.get("players", {}).items()},
            fields={fid: Field.from_dict(f) for fid, f in d.get("fields", {}).items()},
            roll=RollState.from_dict(d.get("roll", {})),
            board=BoardPhaseState.from_dict(d.get("board", {})),
            cards=CardState.from_dict(d.get("cards", {})),
        )
