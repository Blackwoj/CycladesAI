from ....abstract_models.abstract_base_model import AbstractModelClass


class PosejdonReqModel(AbstractModelClass):

    def __init__(self):
        self._model = None

    @property
    def model_name(self):
        return "PosejdonReqModel"

    @property
    def action_outputs(self) -> list[int]:
        """Returns number of outputs: 1
        1. target water
        """

        return [61]
