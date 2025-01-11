from pathlib import Path
from ..specific_models.common_models.build_model import BuildModel
from abc import abstractmethod
from .AbstractModelClassDL import SimpleNNModel
from .AbstractModelClassAC import AbstractModelClassAC


class AbstractDecider(SimpleNNModel):

    def __init__(self, build_model: BuildModel) -> None:
        self._build_model = build_model
        self._model = None
        super().__init__()

    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def action_outputs(self):
        raise NotImplementedError

    @abstractmethod
    def load_model(self, location: Path):
        super().load_model(location)

    def save_model(self, location: Path):
        return super().save_model(location)

    def get_action(self, state: list[int]):
        actions_rewards = list(self.get_action_reward(state).values())
        state.extend(actions_rewards)
        model_to_perform = self.output_move(self._choose_action(state))
        if model_to_perform:
            return model_to_perform.model_name, model_to_perform.get_action(state)
        else:
            return "End", []

    def get_action_reward(self, state: list[int]) -> dict[str, int]:
        reward_dict = {}
        for model in self.output_model:
            name, action = model.get_action(state)
            reward = model.predict_reward(state, action)
            if reward:
                reward_dict[name] = int(reward)
        return reward_dict

    def get_highest_reward(self, state: list[int]) -> int:
        highest_reward = -1000000000000
        for model in self.output_model:
            name, action = model.get_action(state)
            reward = model.predict_reward(state, action)
            if reward and reward > highest_reward:
                highest_reward = reward
        return highest_reward

    def output_move(self, output: list):
        for i in range(len(output) - 1):
            if output[i] == 1:
                return self.output_model[i]
        if output[-1]:
            return None
        raise NotImplementedError

    @property
    @abstractmethod
    def output_model(self) -> list[AbstractModelClassAC]:
        raise NotImplementedError
