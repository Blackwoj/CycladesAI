from ....abstract_models.abstract_base_model import AbstractModelClass


class AresMoveModel(AbstractModelClass):

    def __init__(self):
        self._model = None

    @property
    def model_name(self) -> str:
        return "AresMoveModel"
