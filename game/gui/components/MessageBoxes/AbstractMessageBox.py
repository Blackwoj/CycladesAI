from abc import ABC

import pygame

from ...common.Config import Config


class AbstractMessageBox(ABC):

    def __init__(self, screen: pygame.Surface):
        self._screen = screen
        self.load_backgrounds()

    def load_backgrounds(self):
        self._loaded_bg = {}
        sizes = [(500, 300), (250, 150)]
        message_bg_path = Config.app.background_dir / "message.png"
        loaded_img = pygame.image.load(message_bg_path).convert_alpha()
        for size in sizes:
            self._loaded_bg[size] = self.scale_img(loaded_img, size)
        self._multiplayer_icon = {
            i: self.load_and_scale((Config.app.boards_items / "multiplier" / f"{i}.png"), [80, 80])
            for i in range(1, 7)
        }
        self.font = pygame.font.Font(Config.app.assert_dir / "fonts" / "font1.ttf", 18)

    def load_and_scale(self, location, size):
        img = pygame.image.load(location).convert_alpha()
        return self.scale_img(img, size)

    def scale_img(self, image: pygame.Surface, size: list[float]) -> pygame.Surface:
        return pygame.transform.scale(image, size)
