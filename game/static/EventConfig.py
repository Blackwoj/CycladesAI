import pygame


class EventConfig:

    SHOW_BOARD = pygame.USEREVENT + 1
    SHOW_MENU = pygame.USEREVENT + 2
    SHOW_PAUSE = pygame.USEREVENT + 3
    SHOW_ROLL = pygame.USEREVENT + 4
    CHANGE_PAGE = [SHOW_BOARD, SHOW_MENU, SHOW_PAUSE, SHOW_ROLL]
    
