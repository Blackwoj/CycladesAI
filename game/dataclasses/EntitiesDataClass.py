from dataclasses import dataclass
from typing import Optional

@dataclass
class Entity:
    _id: Optional[int] = None
    _type: Optional[str] = None
    quantity: int = 0
