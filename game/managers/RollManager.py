import logging
import random
from enum import Enum

import pygame

from ..DataCache import DataCache
from ..dataclasses.PlayerDataClass import PlayerDataclass
from ..enums.GameState import GameState
from ..gui.common.Config import Config
from ..static.EventConfig import EventConfig
from .AbstractManager import AbstractManager


class RollManager(AbstractManager):

    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self._heros_order = None

    @property
    def stage_type(self) -> Enum:
        return GameState.ROLL

    def read_cache_values(self):
        self._bid_order = DataCache.get_value("bid_order")
        self._act_bids = DataCache.get_value("bids_value")
        self._heros_per_row = DataCache.get_value("heros_per_row")
        self._player_status: dict[str, PlayerDataclass] = DataCache.get_value("player_data")
        super().read_cache_values()

    def save_cache_values(self):
        DataCache.set_value("player_data", self._player_status)
        DataCache.set_value("bid_order", self._bid_order)
        DataCache.set_value("heros_per_row", self._heros_per_row)
        return super().save_cache_values()

    def handle_events(self, event: pygame.event.Event):
        self.read_cache_values()
        if self._act_stage == self.stage_type:
            if not self._act_player and (not self._heros_per_row["row_1"] or not self._bid_order):
                self.config_stage()
            if not self._act_player:
                self.next_player()
            if event.type in EventConfig.ROWS.values():
                self.validate_bid(event.type)
                self.define_roll_results()
            if event.type == EventConfig.APPOLLON_BID:
                self.add_player_to_appollon()
                self.define_roll_results()
        else:
            logging.info("It's not roll stage, nothing will happend!")
        self.save_cache_values()

    def validate_bid(self, event):
        player_coins = self._player_status[self._act_player].coins
        player_priests = self._player_status[self._act_player].priests
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
                elif passed_bid <= player_coins + player_priests and player_coins >= 1:
                    self.updated_bids(row_name, self._act_player, passed_bid)
                    return

    def updated_bids(self, row, player, bid):
        self._act_player = ""
        if self._act_bids[row]:
            self._act_player = self._act_bids[row]["player"]
        self._act_bids[row]["player"] = player
        self._act_bids[row]["bid"] = bid
        if not self._bid_order and not self._act_player:
            self._act_stage = GameState.BOARD

    def add_player_to_appollon(self):
        self._act_bids["row_5"] = self._act_bids["row_5"] + [self._act_player]
        self.next_player()

    def next_player(self):
        if not self._bid_order:
            self._act_stage = GameState.BOARD
            self._act_player = ""
        else:
            self._act_player = self._bid_order[0]
            self._bid_order = self._bid_order[1:]

    def config_stage(self):
        if not self._bid_order:
            self._bid_order = Config.app.players_names[0:DataCache.get_value("num_of_players")]
            random.shuffle(self._bid_order)
        self._withdraw_heros()

    def _withdraw_heros(self):
        heros = []
        left_heros = DataCache.get_value("left_heros")
        av_heros = [element for element in Config.app.heros_names if element not in left_heros]
        random.shuffle(av_heros)
        num_of_players = DataCache.get_value("num_of_players") - 1
        missing_heros_num = num_of_players - len(left_heros)
        heros = left_heros + av_heros[:missing_heros_num]
        DataCache.set_value(
            "left_heros",
            [element for element in Config.app.heros_names if element not in heros]
        )
        random.shuffle(heros)
        temp_heros_order = {}
        for i, key in enumerate(self._heros_per_row.keys()):
            if i < num_of_players:
                temp_heros_order[key] = heros[i]
        self._heros_per_row = temp_heros_order

    def define_roll_results(self):
        if not self._bid_order and not self._act_player:
            board_game_order = DataCache.get_value("play_order")
            players_heros = DataCache.get_value("hero_players")

            for row in self._act_bids.keys():
                if self._act_bids[row]:
                    if row != "row_5":
                        row_hero = self._heros_per_row[row]
                        _player = self._act_bids[row]["player"]
                        board_game_order.append(_player)
                        price = self._act_bids[row]["bid"]
                        pricer_without_priests = price - self._player_status[_player].priests
                        final_cost = 1 if pricer_without_priests <= 0 else pricer_without_priests
                        self._player_status[_player].coins = self._player_status[_player].coins - final_cost
                        players_heros[_player] = row_hero
                    else:
                        for i in range(len(self._act_bids[row])):
                            board_game_order.append(self._act_bids[row][i])
                            players_heros[self._act_bids[row][i]] = "apollon" if i == 0 else "ap_s"
            DataCache.set_value("play_order", board_game_order)
            DataCache.set_value("hero_players", players_heros)
