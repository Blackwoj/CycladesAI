from dataclasses import dataclass
from typing import Optional

@dataclass
class Building:
    hero: str
    location: list
    island: str
    place: Optional[str] = None
