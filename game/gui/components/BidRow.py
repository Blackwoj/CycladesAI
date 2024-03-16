import pygame
from ..common.Config import Config
from ...static.EventConfig import EventConfig
from ...DataChache import DataCache


class BidRow():

    def __init__(self, screen: pygame.Surface, position: list[int], row_id: int):
        self.row_name = "row_" + str(row_id)
        self._screen = screen
        self._act_price = 0
        self.made_bid = 0
        self._position = position

    @property
    def min_price(self):
        return self._act_price + 1

    def valid_bet(self):
        pass

    def build_row(self):
        row = []
        cross_w = pygame.Surface((5, 15))
        cross_w.fill("black")
        cross_h = pygame.Surface((15, 5))
        cross_h.fill("black")
        row = []
        for i in range(0, 10):
            rect = pygame.Rect((i * 30 + self._position[0]), self._position[1], 50, 50)
            row.append(rect)
        for i in range(0, len(row)):
            bid_icon = pygame.image.load(Config.app.assert_dir / "bid_points" / f"{i+1}.png")
            self._screen.blit(self.scale_img(bid_icon, [27, 27]), (row[i].left, row[i].top))
        pos = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()

        for i in range(0, len(row)):
            hit = row[i].collidepoint(pos)

            if hit and pressed[0] == 1:
                pygame.event.post(pygame.event.Event(EventConfig.ROWS[self.row_name]))
                DataCache.set_value("temp_bid", i+1)

    def scale_img(self, image: pygame.Surface, size: list[float]) -> pygame.Surface:
        return pygame.transform.scale(image, size)
