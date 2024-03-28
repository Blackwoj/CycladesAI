import pygame


class Locations:

    roll_background = pygame.Rect(60, 120, 404, 800)
    roll_board_background = pygame.Rect(464, 0, 736, 800)

    heros_board_location = {
        "row_1": pygame.Rect(92, 162, 40, 40),
        "row_2": pygame.Rect(92, 305, 40, 40),
        "row_3": pygame.Rect(92, 445, 40, 40),
        "row_4": pygame.Rect(92, 583, 40, 40),
    }
    appollon_players_locations = [
        pygame.Rect(305, 704, 40, 40),
        pygame.Rect(350, 704, 40, 40),
        pygame.Rect(387, 704, 40, 40),
        pygame.Rect(350, 740, 40, 40),
        pygame.Rect(387, 740, 40, 40),
    ]
    players_bid_order = [
        [80, 30, 80, 80],
        [150, 30, 80, 80],
        [210, 30, 80, 80],
        [270, 30, 80, 80],
        [330, 30, 80, 80]
    ]
