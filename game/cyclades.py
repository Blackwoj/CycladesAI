import pygame

from .enums.GameState import GameState
from .gui.GameGui import ViewManager
from .static.EventConfig import EventConfig
import logging


class GameManager:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1200, 800))
        self.Gui = ViewManager(self.screen)

        self.current_state = GameState.START

    @property
    def _page_connector_dict(self):
        _page_connector = {
            EventConfig.SHOW_MENU: GameState.START,
            EventConfig.SHOW_BOARD: GameState.BOARD,
            EventConfig.SHOW_PAUSE: GameState.PAUSE,
            EventConfig.SHOW_ROLL: GameState.ROLL
        }
        return _page_connector

    @property
    def _handle_event_dict(self):
        _handle_event = {
            GameState.START: self.handle_menu_input,
            GameState.BOARD: self.handle_gameplay_input,
            GameState.PAUSE: self.handle_pause_input,
            GameState.GAME_OVER: self.handle_game_over_input,
            GameState.ROLL: self.handle_roll_input
        }
        return _handle_event[self.current_state]

    def start(self):
        while True:
            self.handle_events()
            self.update()
            self.render()

    # Handle any input events
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            elif event.type == pygame.KEYDOWN:
                self._handle_event_dict(event.key)
            elif event.type in EventConfig.CHANGE_PAGE:
                self._change_page(event)

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
            self.current_state = GameState.BOARD
        elif key == pygame.K_2:  # quit game
            self.quit_game()

    # Handle input events in the GAMEPLAY state
    def handle_gameplay_input(self, key):
        if key == pygame.K_p:  # pause
            self.current_state = GameState.PAUSE

    # Handle input events in the PAUSE state
    def handle_pause_input(self, key):
        if key == pygame.K_p:  # resume gameplay
            self.current_state = GameState.BOARD
        elif key == pygame.K_q:  # quit game
            self.quit_game()    # Handle input events in the PAUSE state

    def handle_roll_input(self, key):
        if key == pygame.K_p:  # resume gameplay
            self.current_state = GameState.BOARD
        elif key == pygame.K_q:  # quit game
            self.quit_game()

    # Handle input events in the GAME_OVER state
    def handle_game_over_input(self, key):
        if key == pygame.K_r:  # restart game
            self.current_state = GameState.START

    # Update the game state
    def update(self):
        if self.current_state == GameState.BOARD:
            # game logic and update here
            pass

    # Render the current state
    def render(self):
        self.screen.fill((0, 0, 0))  # clear screen

        if self.current_state == GameState.START:
            self.Gui.show_menu()
        elif self.current_state == GameState.BOARD:
            self.Gui.show_board()
        elif self.current_state == GameState.PAUSE:
            self.render_pause()
        elif self.current_state == GameState.GAME_OVER:
            self.render_game_over()

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
