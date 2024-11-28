from ....abstract_models.abstract_base_model import AbstractModelClass


class AresReqModel(AbstractModelClass):

    def __init__(self):
        self._model = None

    @property
    def model_name(self):
        return "AresReqModel"

    @property
    def action_outputs(self) -> list[int]:
        """Returns number of outputs: 1
        1. target island (1-13)
        """

        return [13]

    def get_action(self, state):
        return self.model_name, self._choose_action(state)
