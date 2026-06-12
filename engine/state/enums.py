from __future__ import annotations

from enum import Enum


class Stage(Enum):
    """Etap gry. Odpowiednik starego GameState, bez stanów GUI (PAUSE itp.)."""
    SETUP = "setup"
    ROLL = "roll"
    BOARD = "board"
    GAME_OVER = "game_over"


class FieldType(Enum):
    ISLAND = "island"
    WATER = "water"


class HEROES:
    """Stałe nazwy herosów (parytet z game.gui...AppSection.heros_names)."""
    ARES = "ares"
    ATENA = "atena"
    POSEJDON = "posejdon"
    ZEUS = "zeus"
    APOLLON = "apollon"

    BIDDABLE = (ARES, ATENA, POSEJDON, ZEUS)
    # mapowanie heros budynku -> int (parytet z AbstractDataclass._hero_building_to_int)
    BUILDING_ID = {ARES: 1, ATENA: 2, POSEJDON: 3, ZEUS: 4}
