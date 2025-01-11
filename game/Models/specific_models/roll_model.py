class RollModel():

    def __init__(self, move_models: dict) -> None:
        self.move_models = move_models
        pass

    def predict(self, state: list[int], bids: dict[str, list]):
        for key in bids.keys():
            bids[key][1] += 1
        bid_row = ""
        highest_reward = -1000000000
        for hero, model in self.move_models.items():
            if hero == "apollon":
                continue
            step_after_win = state
            price = 1
            row = ""
            for _row, data in bids.items():
                if data[0] == hero:
                    price = data[1]
                    row = _row
            if not row:
                raise NotImplementedError
            step_after_win[self.player_coins_index(state[-1])] -= price
            if step_after_win[self.player_coins_index(state[-1])] >= 0:
                reward = model.get_highest_reward(state)
                print(row, reward)
                if reward > highest_reward:
                    bid_row = row
                    highest_reward = reward

    @staticmethod
    def player_coins_index(player_id) -> int:
        id_coins_index = [
            287,
            290,
            293,
            296,
            299
        ]
        return id_coins_index[player_id - 1]
