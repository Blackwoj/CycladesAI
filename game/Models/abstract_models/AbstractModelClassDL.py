from keras import layers, models, optimizers
from .AbstractModel import AbstractModel
from abc import abstractmethod
import logging
from pathlib import Path
from ..Config import Config


class SimpleNNModel(AbstractModel):
    def __init__(self):
        super().__init__()
        self._model = self.build_model()

    @property
    @abstractmethod
    def action_outputs(self) -> list[int]:
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    def build_model(self):
        state_input = layers.Input(shape=(self.state_size,))

        x = layers.Dense(64, activation="relu")(state_input)
        x = layers.Dense(64, activation="relu")(x)

        outputs = []
        for output_size in self.action_outputs:
            outputs.append(layers.Dense(output_size, activation="softmax")(x))

        _model = models.Model(inputs=state_input, outputs=outputs)
        _model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),  # type: ignore
            loss="categorical_crossentropy",  # Dla klasyfikacji
            metrics=["accuracy"]
        )
        return _model

    def train(self, states, actions, epochs=10, batch_size=32):
        """
        Trenuje _model na podstawie danych.
        - states: Tablica stanów wejściowych (Nxstate_size)
        - actions: Oczekiwane akcje (Nxaction_outputs w formie one-hot)
        """
        self._model.fit(states, actions, epochs=epochs, batch_size=batch_size)  # type: ignore

    def predict(self, state):
        """
        Przewiduje akcję na podstawie stanu.
        - state: Pojedynczy stan (wektor o rozmiarze state_size)
        """
        state = state.reshape(1, -1)  # Dopasowanie wymiaru wejścia
        return self._model.predict(state)  # type: ignore

    def save_model(self, filepath: Path):
        """Zapisuje _model na dysk."""
        self._model.save(filepath)  # type: ignore

    def load_model(self, filepath: Path):
        """Ładuje _model z pliku."""
        model_path_action = filepath / (self.model_name + "_action" + Config.model_extension)
        if model_path_action.exists():
            self._model.save(filepath)
        else:
            self._model = self.build_model()

    def _choose_action(self, state: list[int]) -> list[int]:
        if not self._model:
            logging.error("%s missing", self.model_name)
            return []
        return self._model.predict(state)
