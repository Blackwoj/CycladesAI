from dataclasses import dataclass
from typing import Optional


@dataclass
class Field:
    type: str
    owner: str
    quantity: int
    base_income: int
    small_building: Optional[dict[str, str]] = None
    metropolis: bool = False
    income: int = 0
