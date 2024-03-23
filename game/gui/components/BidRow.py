import pygame

from ...DataChache import DataCache
from ...static.EventConfig import EventConfig
from ..common.Config import Config


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
        act_bids = DataCache.get_value("bids_value")[self.row_name]

        if act_bids:
            player_bidder = pygame.image.load(
                Config.app.players_icons / (act_bids["player"] + ".png")
            )
            bid_value = act_bids["bid"]

        pos = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed()
        dec_value = 0

        if act_bids and bid_value >= 10:
            dec_value = int(bid_value / 10)
            dec_value_img = pygame.image.load(Config.app.bid_icon_dir / f"10_{dec_value}.png")
            rect = pygame.Rect((315 + self._position[0]), self._position[1], 27, 27)
            self._screen.blit(
                self.scale_img(dec_value_img, [rect.width, rect.height]),
                (rect.left, rect.top)
            )

        for i in range(0, 10):
            rect = pygame.Rect((i * 30 + self._position[0]), self._position[1], 27, 27)

            hit = rect.collidepoint(pos)

            if hit and pressed[0] == 1:
                pygame.event.post(pygame.event.Event(EventConfig.ROWS[self.row_name]))
                DataCache.set_value("temp_bid", i + 1 + 10 * dec_value)

            bid_icon = pygame.image.load(Config.app.bid_icon_dir / f"{i+1}.png")

            if act_bids and i + 1 + 10 * dec_value == bid_value:
                bid_icon = player_bidder
            if act_bids and dec_value * 10 == bid_value and i == 9:
                bid_icon = player_bidder
            self._screen.blit(
                self.scale_img(bid_icon, [rect.width, rect.height]),
                (rect.left, rect.top)
            )

    def scale_img(self, image: pygame.Surface, size: list[float]) -> pygame.Surface:
        return pygame.transform.scale(image, size)
