import pygame


class Locations:

    roll_background = pygame.Rect(60, 0, 404, 800)
    roll_board_background = pygame.Rect(464, 0, 736, 800)

    heros_board_location = {
        "row_1": pygame.Rect(87, 120 + 37 + 2, 40, 40),
        "row_2": pygame.Rect(87, 255 + 37 + 2, 40, 40),
        "row_3": pygame.Rect(87, 390 + 37 + 2, 40, 40),
        "row_4": pygame.Rect(87, 525 + 37 + 2, 40, 40),
    }
    appollon_players_locations = [
        pygame.Rect(360, 687, 38, 38),
        pygame.Rect(421, 686, 38, 38),
        pygame.Rect(471, 685, 38, 38),
        pygame.Rect(421, 730, 38, 38),
        pygame.Rect(471, 728, 38, 38),
    ]
    players_bid_order = [
        [88, 28, 80, 80],
        [177, 28, 80, 80],
        [267, 30, 80, 80],
        [356, 30, 80, 80],
        [445, 30, 80, 80]
    ]
