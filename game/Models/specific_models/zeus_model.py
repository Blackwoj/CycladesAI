from ..abstract_models.abstract_decider_model import AbstractDecider
from .common_models.build_model import BuildModel


class ZeusModel(AbstractDecider):

    def __init__(self, build_model: BuildModel) -> None:
        super().__init__(build_model)

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
