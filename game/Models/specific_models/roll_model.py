from ..abstract_models.abstract_base_model import AbstractModelClass


class RollModel(AbstractModelClass):

    @property
    def model_name(self) -> str:
        return "RollModel"

    @property
    def action_outputs(self) -> list[int]:
        """Returns number of outputs
        1. Hero to bid(1 - 5)
        3. Price(1- 100)
        """
        return [5, 100]

    def get_action(self, state):
        return self._choose_action(state)
