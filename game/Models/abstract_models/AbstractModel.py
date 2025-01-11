from pathlib import Path
from abc import abstractmethod


class AbstractModel:

    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def action_outputs(self) -> list[int]:
        raise NotImplementedError

    @property
    def state_size(self):
        return 300

    @abstractmethod
    def get_action(self):
        raise NotImplementedError

    @abstractmethod
    def train(self):
        raise NotImplementedError

    @abstractmethod
    def predict(self):
        raise NotImplementedError

    @abstractmethod
    def save_model(self, location: Path):
        raise NotImplementedError
