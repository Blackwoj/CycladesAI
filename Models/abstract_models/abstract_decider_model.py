from pathlib import Path
from ..specific_models.common_models.build_model import BuildModel
from abc import abstractmethod
from .abstract_base_model import AbstractModelClass


class AbstractDecider(AbstractModelClass):

    def __init__(self, build_model: BuildModel) -> None:
        self._build_model = build_model
        self._model = None

    @abstractmethod
    def load_model(self, location: Path):
        super().load_model(location)

    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def action_outputs(self):
        raise NotImplementedError

    def save_model(self, location: Path):
        return super().save_model(location)
