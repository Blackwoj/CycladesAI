from dataclasses import dataclass


@dataclass
class Income:
    quantity: int
    location: str = ""
    _type = "income"
