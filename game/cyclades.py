from pathlib import Path

import pygame

from .components.button import Button
from .enums.GameState import GameState


class GameManager:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1200, 800))

        self.current_state = GameState.START

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
                if self.current_state == GameState.START:
                    self.handle_menu_input(event.key)
                elif self.current_state == GameState.BOARD:
                    self.handle_gameplay_input(event.key)
                elif self.current_state == GameState.PAUSE:
                    self.handle_pause_input(event.key)
                elif self.current_state == GameState.GAME_OVER:
                    self.handle_game_over_input(event.key)

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
            self.render_menu()
        elif self.current_state == GameState.BOARD:
            self.render_gameplay()
        elif self.current_state == GameState.PAUSE:
            self.render_pause()
        elif self.current_state == GameState.GAME_OVER:
            self.render_game_over()

        pygame.display.flip()  # update screen

    # Render the menu screen
    def render_menu(self):
        bg = pygame.image.load(Path(__file__).resolve().parent/"assets"/"menu_bg.png")

        scaled_bg = pygame.transform.scale(bg, (self.screen.get_width(), self.screen.get_height()))
        self.screen.blit(scaled_bg, (0, 0))

        img_path = Path(__file__).resolve().parent / 'assets'
        self.button = Button(
            self.screen,
            img_path,
            pygame.Rect(100, 100, 200, 200),
            self.play
        )
        self.button.update()
        pygame.display.update()
        pass

    def play(self):
        print("Clicked!")
        pass

    # Render the gameplay screen
    def render_gameplay(self):
        self.screen.fill((255, 255, 255))
        # render gameplay here
        pass

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
