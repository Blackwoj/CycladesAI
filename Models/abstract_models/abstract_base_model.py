from pathlib import Path
import keras
from ..Config import Config
from abc import abstractmethod


class AbstractModelClass:

    def __init__(self):
        self._model = None

    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    def load_model(self, location: Path):

        self._model = keras.models.load_model(location / self.model_name / Config.model_extension)

    @abstractmethod
    def train(self):
        raise NotImplementedError

    @abstractmethod
    def predict(self):
        raise NotImplementedError
