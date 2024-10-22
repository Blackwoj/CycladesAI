from dataclasses import dataclass


@dataclass
class Income:
    quantity: int
    _id: int = 2
    _type = "income"
