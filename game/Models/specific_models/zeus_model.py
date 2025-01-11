from .common_models.build_model import BuildModel
from ..abstract_models.AbstractModelClassAC import AbstractModelClassAC
from typing import Optional


class ZeusModel(AbstractModelClassAC):

    def __init__(self, build_model: BuildModel) -> None:
        self._build_model = build_model
        super().__init__()

    @property
    def model_name(self) -> str:
        return "ZeusDeciderModel"

    @property
    def action_outputs(self) -> list[int]:
        """Returns number of outputs
        1. Buy card(0 - 1)
        3. Build building(0 - 1)
        4. End round(0 - 1)
        """
        return [1, 1, 1]

    def get_action(self, state):
        decision = self._choose_action(state)
        if decision[0]:
            return "Buy Card", []
        elif decision[1]:
            return self._build_model.model_name, self._build_model.get_action(state)
        elif decision[2]:
            return "End", []
        raise NotImplementedError

    def get_highest_reward(self, state: list[int]) -> Optional[int]:
        return self.predict_reward(state, self._choose_action(state))
