from dataclasses import dataclass


@dataclass
class AbstractDataclass:
    @staticmethod
    def _player_to_int(player):
        player_id = {
            "None": 0,
            "p1": 1,
            "p2": 2,
            "p3": 3,
            "p4": 4,
            "p5": 5
        }
        return player_id[player]

    @staticmethod
    def _hero_building_to_int(hero):
        hero_id = {
            "ares": 1,
            "atena": 2,
            "posejdon": 3,
            "zeus": 4
        }
        return hero_id[hero]
