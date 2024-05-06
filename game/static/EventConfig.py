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
        "row_4": ROW_4_BID,
    }

    UPDATE_WARRIOR_POS = pygame.USEREVENT + 11
    UPDATE_SHIP_POS = pygame.USEREVENT + 12
    SHOW_MULTIPLY_OPTIONS_WAR = pygame.USEREVENT + 13
    SHOW_MULTIPLY_OPTIONS_SHIP = pygame.USEREVENT + 14

    NEW_BUILDING = pygame.USEREVENT + 15
    NEW_WARRIOR = pygame.USEREVENT + 16
    NEW_SHIP = pygame.USEREVENT + 17

    BOARD_SECTION = [UPDATE_WARRIOR_POS, UPDATE_SHIP_POS]
