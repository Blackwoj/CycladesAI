from dataclasses import dataclass


@dataclass
class Entity:
    _type: str
    owner: str
    quantity: int
    location: str
