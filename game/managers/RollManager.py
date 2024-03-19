import pygame
from ..DataChache import DataCache
from ..enums.GameState import GameState
import logging
from ..static.EventConfig import EventConfig
from ..gui.common.Config import Config
import random


class RollManager():

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.bid_order = []

    @property
    def stage_type(self):
        return GameState.ROLL

    def handle_events(self, event):
        if not DataCache.get_value("bid_order"):
            bid_order = Config.app.players_names[0:DataCache.get_value("num_of_players")]
            random.shuffle(bid_order)
            print(bid_order)
            DataCache.set_value("bid_order", bid_order)

        if DataCache.get_value("act_stage") == self.stage_type:
            if event.type in EventConfig.ROWS.values():
                self.validate_bid(event.type)

        else:
            logging.info("It's not roll stage, nothing will happend!")
        pass

    def validate_bid(self, event):
        player = DataCache.get_value("act_player")
        for row_name, row_event in EventConfig.ROWS.items():
            if event == row_event:
                passed_bid = DataCache.get_value("temp_bid")
                if DataCache.get_value("bids_value")[row_name]:
                    row_owner, bid_value = DataCache.get_value("bids_value")[row_name].items()
                    row_owner = row_owner[1]
                    bid_value = bid_value[1]
                else:
                    self.updated_bids(row_name, player, passed_bid)
                    print("Valid bid 1")
                    return
                if (
                    bid_value < passed_bid
                    and passed_bid <= DataCache.get_value("coins")[player] + DataCache.get_value("priests")[player]
                    and row_owner != player
                ):
                    self.updated_bids(row_name, player, passed_bid)
                else:
                    print("invalid bid")

    def updated_bids(self, row, player, bid):
        act_bids = DataCache.get_value("bids_value")
        act_bids[row]["player"] = player
        act_bids[row]["bid"] = bid
        DataCache.set_value("bids_value", act_bids)
