"""Typy akcji — jawna reprezentacja ruchu gracza.

Zastępuje niejawny ruch ze starego kodu (drag&drop + pygame.event.post).
Każda akcja jest:
- niezmienna (frozen) i hashowalna — wygodne dla węzłów MCTS,
- serializowalna (to_dict / action_from_dict) — pod logi, reprodukcję i FastAPI.

`PlayCard` istnieje od początku jako SZEW pod moduł kart specjalnych (Faza 7),
mimo że rejestr kart jest na razie pusty.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field as dc_field


@dataclass(frozen=True)
class Action:
    """Baza. Pole `type` służy do serializacji/dyskryminacji."""
    type: str = dc_field(default="action", init=False)

    def to_dict(self) -> dict:
        return {"type": self.type, **{k: v for k, v in asdict(self).items() if k != "type"}}


@dataclass(frozen=True)
class RollBid(Action):
    """Licytacja herosa w danym rzędzie aukcji."""
    type: str = dc_field(default="roll_bid", init=False)
    player: str = ""
    row: str = ""
    amount: int = 0


@dataclass(frozen=True)
class ApollonBid(Action):
    """Dołączenie do rzędu Apollona (row_5)."""
    type: str = dc_field(default="apollon_bid", init=False)
    player: str = ""


@dataclass(frozen=True)
class PlaceEntity(Action):
    """Wystawienie nowej jednostki (wojownik/statek) na pole."""
    type: str = dc_field(default="place_entity", init=False)
    player: str = ""
    field_id: str = ""
    kind: str = ""        # "warrior" | "ship"
    quantity: int = 1


@dataclass(frozen=True)
class MoveEntity(Action):
    """Przesunięcie jednostek między polami."""
    type: str = dc_field(default="move_entity", init=False)
    player: str = ""
    from_field: str = ""
    to_field: str = ""
    quantity: int = 1
    kind: str = ""  # "warrior" | "ship" | "" (wykrywane z pola źródłowego)


@dataclass(frozen=True)
class Build(Action):
    """Postawienie budynku herosa na wyspie."""
    type: str = dc_field(default="build", init=False)
    player: str = ""
    field_id: str = ""
    hero: str = ""


@dataclass(frozen=True)
class BuyCard(Action):
    """Zakup karty filozofa (Atena) / kapłana (Zeus)."""
    type: str = dc_field(default="buy_card", init=False)
    player: str = ""
    hero: str = ""        # "atena" | "zeus"


@dataclass(frozen=True)
class PlayCard(Action):
    """Zagranie karty specjalnej. SZEW pod przyszły moduł kart (Faza 7)."""
    type: str = dc_field(default="play_card", init=False)
    player: str = ""
    card_id: str = ""
    targets: tuple = ()


@dataclass(frozen=True)
class EndTurn(Action):
    """Zakończenie tury bieżącego gracza."""
    type: str = dc_field(default="end_turn", init=False)
    player: str = ""


_REGISTRY = {
    "roll_bid": RollBid,
    "apollon_bid": ApollonBid,
    "place_entity": PlaceEntity,
    "move_entity": MoveEntity,
    "build": Build,
    "buy_card": BuyCard,
    "play_card": PlayCard,
    "end_turn": EndTurn,
}


def action_from_dict(d: dict) -> Action:
    """Odtwórz akcję z dict (np. z requestu HTTP albo logu)."""
    payload = {k: v for k, v in d.items() if k != "type"}
    cls = _REGISTRY[d["type"]]
    if "targets" in payload and isinstance(payload["targets"], list):
        payload["targets"] = tuple(payload["targets"])
    return cls(**payload)
