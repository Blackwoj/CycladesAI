from dataclasses import dataclass


@dataclass
class Income:
    location: str
    quantity: int
    _type = "income"
