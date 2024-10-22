import logging

from game.cyclades import GameManager


logging.getLogger(__name__)
logging.basicConfig(
    encoding='utf-8',
    level=logging.DEBUG,
    format='%(asctime)s %(filename)s %(lineno)d [%(levelname)s]: %(message)s'
)

if __name__ == "__main__":
    game_state_manager = GameManager()
    game_state_manager.start()
