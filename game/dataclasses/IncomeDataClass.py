from dataclasses import dataclass


@dataclass
class Income:
    quantity: int
    _type = "income"
