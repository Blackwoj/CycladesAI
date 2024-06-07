from dataclasses import dataclass


@dataclass
class Field:
    type: str
    owner: str
    quantity: int
    base_income: int
    small_building: dict = None
    metropolis: bool = False
    income: int = 0
