import logging

import pygame

from .DataCache import DataCache
from .enums.GameState import GamePages, GameState
from .gui.GameGui import ViewManager
from .managers.BoardManager import BoardManager
from .managers.RollManager import RollManager
from .static.EventConfig import EventConfig
from .gui.common.Config import Config
from .connector.Model_connector import ConnectModel


class GameManager:

    def __init__(self):
        pygame.init()
        DataCache.initialize_cache()
        self.screen = pygame.display.set_mode((1081, 800))
        self.Gui = ViewManager(self.screen)
        self.RollManager = RollManager(self.screen)
        self.BoardManager = BoardManager(self.screen)
        self.current_state = GamePages.START
        self.model_connector = ConnectModel()
        DataCache.set_value("act_stage", GameState.ROLL)

    @property
    def _page_connector_dict(self):
        _page_connector = {
            EventConfig.SHOW_MENU: GamePages.START,
            EventConfig.SHOW_BOARD: GamePages.BOARD,
            EventConfig.SHOW_PAUSE: GamePages.PAUSE,
            EventConfig.SHOW_ROLL: GamePages.ROLL
        }
        return _page_connector

    @property
    def _handle_event_dict(self):
        _handle_event = {
            GamePages.START: self.handle_menu_input,
            GamePages.BOARD: self.handle_gameplay_input,
            GamePages.PAUSE: self.handle_pause_input,
            GamePages.GAME_OVER: self.handle_game_over_input,
            GamePages.ROLL: self.handle_roll_input
        }
        return _handle_event[self.current_state]

    def start(self):
        while True:
            self.render()
            self.handle_events()

    # Handle any input events
    def handle_events(self):
        events = pygame.event.get()
        if not events and DataCache.get_value("act_player") in Config.app.ai_player:
            # TODO add run algorithm for AI
            self.model_connector.predict_state()
            pass
        if events and DataCache.get_value("act_player") in Config.app.train_ai_player and not DataCache.get_value("move_train_data"):
            self.model_connector.save_pre_state()
        for event in events:
            if event.type == pygame.QUIT:
                self.quit_game()
            elif event.type in EventConfig.CHANGE_PAGE:
                self._change_page(event)
            else:
                self._handle_event_dict(event)
        if DataCache.get_value("ai_move_success"):
            self.model_connector.train_on_state()
            pass
        if DataCache.get_value("move_train_data"):
            self.model_connector.train_on_state()

    def _change_page(self, event: pygame.event.Event):
        """Handle change page event

        :param event: Special USEREVENT connected with page
        """
        if event.type in self._page_connector_dict.keys():
            self.current_state = self._page_connector_dict[event.type]
        else:
            logging.error(f"Unknown page event: {event}")
        self.render()

    # Handle input events in the MENU state
    def handle_menu_input(self, key):
        if key == pygame.K_1:  # start gameplay
            self.current_state = GamePages.BOARD
        elif key == pygame.K_2:  # quit game
            self.quit_game()

    # Handle input events in the GAMEPLAY state
    def handle_gameplay_input(self, event):
        self.BoardManager.handle_events(event)

    # Handle input events in the PAUSE state
    def handle_pause_input(self, key):
        if key == pygame.K_p:  # resume gameplay
            self.current_state = GamePages.BOARD
        elif key == pygame.K_q:  # quit game
            self.quit_game()    # Handle input events in the PAUSE state

    def handle_roll_input(self, event):
        self.RollManager.handle_events(event)

    # Handle input events in the GAME_OVER state
    def handle_game_over_input(self, key):
        if key == pygame.K_r:  # restart game
            self.current_state = GamePages.START

    # Render the current state
    def render(self):
        self.screen.fill((0, 0, 0))  # clear screen

        if self.current_state == GamePages.START:
            self.Gui.show_menu()
        elif self.current_state == GamePages.BOARD:
            self.Gui.show_board()
        elif self.current_state == GamePages.PAUSE:
            self.render_pause()
        elif self.current_state == GamePages.GAME_OVER:
            self.render_game_over()
        elif self.current_state == GamePages.ROLL:
            self.Gui.show_roll()

        pygame.display.flip()  # update screen

    # Render the pause screen
    def render_pause(self):
        # render pause here
        pass

    # Render the game over screen
    def render_game_over(self):
        # render game over here
        pass

    # Quit the game
    def quit_game(self):
        pygame.quit()
        quit()
