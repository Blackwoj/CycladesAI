from dataclasses import dataclass


@dataclass
class Water:
    owner: str
    num_of_entities: int
    base_income: int


@dataclass
class Island(Water):
    income: int
    small_building: dict
    metropolis: bool
