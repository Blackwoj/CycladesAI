import logging
import random

import pygame

from ..DataChache import DataCache
from ..enums.GameState import GameState
from ..gui.common.Config import Config
from ..static.EventConfig import EventConfig


class RollManager():

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.bid_order = []

    @property
    def stage_type(self):
        return GameState.ROLL

    def read_data_cache_values(self):
        self._act_stage = DataCache.get_value("act_stage")
        self._bid_order = DataCache.get_value("bid_order")
        self._act_bids = DataCache.get_value("bids_value")
        self._act_player = DataCache.get_value("act_player")
        self._num_of_player = DataCache.get_value("num_of_players")
        self._heros_per_row = DataCache.get_value("heros_per_row")
        self._left_heros = DataCache.get_value("left_heros")

    def save_data_cache_values(self):
        DataCache.set_value("act_stage", self._act_stage)
        DataCache.set_value("bid_order", self._bid_order)
        DataCache.set_value("act_player", self._act_player)
        DataCache.set_value("num_of_players", self._num_of_player)
        DataCache.set_value("heros_per_row", self._heros_per_row)
        DataCache.set_value("left_heros", self._left_heros)

    def handle_events(self, event):
        self.read_data_cache_values()
        if self._act_stage == self.stage_type:
            if not self._bid_order:
                self._bid_order = Config.app.players_names[0:self._num_of_player]
                random.shuffle(self._bid_order)
            if not self._act_player:
                self._act_player = self._bid_order[0]
                self._bid_order = self._bid_order[1:]
            # if not self._heros_per_row["row_1"]:
            #     if self._num_of_player != 5:
            #         heros = DataCache.get_value("left_heros")
            #         additional_heros = Config.app.heros_names - heros
            #         random.shuffle(additional_heros)
            #         act_heros = heros + additional_heros[:(len(heros)-)]

            if event.type in EventConfig.ROWS.values():
                self.validate_bid(event.type)
        else:
            logging.info("It's not roll stage, nothing will happend!")
        self.save_data_cache_values()

    def validate_bid(self, event):
        player_coins = DataCache.get_value("coins")[self._act_player]
        player_priests = DataCache.get_value("priests")[self._act_player]
        for row_name, row_event in EventConfig.ROWS.items():
            if event == row_event:
                passed_bid = DataCache.get_value("temp_bid")
                if self._act_bids[row_name]:
                    row_owner, bid_value = self._act_bids[row_name].items()
                    row_owner = row_owner[1]
                    bid_value = bid_value[1]
                    if (
                        bid_value < passed_bid
                        and passed_bid <= player_coins + player_priests
                        and row_owner != self._act_player
                        and player_coins >= 1
                    ):
                        self.updated_bids(row_name, self._act_player, passed_bid)
                    else:
                        print("invalid bid")
                elif passed_bid <= player_coins + player_priests and player_coins >= 1:
                    self.updated_bids(row_name, self._act_player, passed_bid)
                    print("Valid bid 1")
                    return
                else:
                    print("invalid bid, no money")

    def updated_bids(self, row, player, bid):
        self._act_player = ""
        if self._act_bids[row]:
            self._act_player = self._act_bids[row]["player"]
        self._act_bids[row]["player"] = player
        self._act_bids[row]["bid"] = bid
        if not DataCache.get_value("bid_order") and not DataCache.get_value("act_player"):
            DataCache.set_value("act_stage", GameState.BOARD)
