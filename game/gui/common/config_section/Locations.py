import pygame


class Locations:

    roll_background = pygame.Rect(60, 120, 404, 800)
    roll_board_background = pygame.Rect(464, 0, 736, 800)

    heros_board_location = {
        "row_1": pygame.Rect(95, 160, 40, 40),
        "row_2": pygame.Rect(95, 305, 40, 40),
        "row_3": pygame.Rect(95, 450, 40, 40),
        "row_4": pygame.Rect(95, 600, 40, 40),
    }
    appollon_players_locations = [
        pygame.Rect(320, 720, 40, 40),
        pygame.Rect(360, 720, 40, 40),
        pygame.Rect(400, 720, 40, 40),
        pygame.Rect(360, 760, 40, 40),
        pygame.Rect(400, 760, 40, 40),
    ]
    players_bid_order = [
        [80, 30, 80, 80],
        [150, 30, 80, 80],
        [210, 30, 80, 80],
        [270, 30, 80, 80],
        [330, 30, 80, 80]
    ]
