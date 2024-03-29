import pygame


class EventConfig:

    SHOW_BOARD = pygame.USEREVENT + 1
    SHOW_MENU = pygame.USEREVENT + 2
    SHOW_PAUSE = pygame.USEREVENT + 3
    SHOW_ROLL = pygame.USEREVENT + 4
    CHANGE_PAGE = [SHOW_BOARD, SHOW_MENU, SHOW_PAUSE, SHOW_ROLL]

    PLAYER_END = pygame.USEREVENT + 5

    ROW_1_BID = pygame.USEREVENT + 6
    ROW_2_BID = pygame.USEREVENT + 7
    ROW_3_BID = pygame.USEREVENT + 8
    ROW_4_BID = pygame.USEREVENT + 9
    APPOLLON_BID = pygame.USEREVENT + 10
    ROWS = {
        "row_1": ROW_1_BID,
        "row_2": ROW_2_BID,
        "row_3": ROW_3_BID,
        "row_4": ROW_4_BID
    }
