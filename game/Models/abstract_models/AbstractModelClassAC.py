from pathlib import Path
import keras
from keras import layers, optimizers, models
from ..Config import Config
from abc import abstractmethod
import numpy as np
import tensorflow as tf
import logging
from typing import Optional, cast
from .AbstractModel import AbstractModel


class AbstractModelClassAC(AbstractModel):

    def __init__(self):
        super().__init__()
        self._model_action: Optional[models.Model] = None
        self._model_critic: Optional[models.Model] = None

    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def action_outputs(self) -> list[int]:
        raise NotImplementedError

    @abstractmethod
    def value_moves(self, state):
        raise NotImplementedError

    @property
    def state_size(self):
        return 305

    def common_input(self):
        return keras.Input(shape=(self.state_size,))

    def load_model(self, location: Path):
        """Ładowanie modeli Aktora i Krytyka z plików"""
        model_path_action = location / (self.model_name + "_action" + Config.model_extension)
        model_path_critic = location / (self.model_name + "_critic" + Config.model_extension)

        if model_path_action.exists() and model_path_critic.exists():
            self._model_action = cast(models.Model, models.load_model(model_path_action))
            self._model_critic = cast(models.Model, models.load_model(model_path_critic))
        else:
            self.get_model()

    def get_model(self):
        """ Zwraca lub buduje modele Aktora i Krytyka """
        if self._model_action is None or self._model_critic is None:
            self._model_action = self.build_actor()
            self._model_critic = self.build_critic()
        return self._model_action, self._model_critic

    def build_actor(self):
        state_input = self.common_input()
        x = layers.Dense(64, activation="relu")(state_input)
        x = layers.Dense(64, activation="relu")(x)

        outputs = []
        for output_size in self.action_outputs:
            outputs.append(layers.Dense(output_size, activation="softmax")(x))

        actor_model = models.Model(inputs=state_input, outputs=outputs)
        actor_model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),  # type: ignore
            loss="categorical_crossentropy"
        )  # type: ignore
        return actor_model

    def build_critic(self):
        state_input = self.common_input()
        action_input = layers.Input(shape=(len(self.action_outputs),))

        x = layers.Concatenate()([state_input, action_input])
        x = layers.Dense(64, activation="relu")(x)
        x = layers.Dense(64, activation="relu")(x)
        value_output = layers.Dense(1, activation="linear")(x)

        critic_model = models.Model(inputs=[state_input, action_input], outputs=value_output)
        critic_model.compile(optimizer=optimizers.Adam(learning_rate=0.001), loss="mse")  # type: ignore
        return critic_model

    @abstractmethod
    def get_action(self, state: list[int]):
        raise NotImplementedError

    def _choose_action(self, state):
        state = np.expand_dims(state, axis=0)
        if self._model_action is None:
            logging.error("No action model for %s", self.model_name)
            self._model_action = self.build_actor()

        predictions = self._model_action.predict(state)

        return predictions

    def train(self, state, reward, gamma=0.99):
        """
        Uczy zarówno aktora, jak i krytyka na podstawie rzeczywistych akcji.
        """
        if not self._model_action or not self._model_critic:
            logging.error("One of the models is missing")
            return

        # Dodanie wymiaru dla batcha
        state = np.expand_dims(state, axis=0)

        # 1. Predykcja akcji za pomocą modelu aktora
        action_probs = self._model_action.predict(state)  # Dystrybucja prawdopodobieństw
        sampled_actions = [
            np.random.choice(len(probs[0]), p=probs[0]) for probs in action_probs
        ]

        # 2. Tworzenie one-hot dla każdej przestrzeni akcji
        action_one_hot = []
        for i, act in enumerate(sampled_actions):
            one_hot = np.zeros(self.action_outputs[i])  # Tworzenie one-hot
            one_hot[act] = 1
            action_one_hot.append(one_hot)
        action_one_hot = np.concatenate(action_one_hot)

        # 3. Obliczenie wartości stanu-akcji przez krytyka
        value = self._model_critic.predict([state, np.expand_dims(action_one_hot, axis=0)])

        # 4. Obliczenie wartości docelowej (target value)
        target_value = reward + gamma * value

        # 5. Trening krytyka
        critic_loss = self._model_critic.train_on_batch(
            [state, np.expand_dims(action_one_hot, axis=0)],
            np.array([[target_value]])
        )

        # 6. Obliczanie przewagi (advantage)
        advantage = target_value - value

        # 7. Trening aktora
        with tf.GradientTape() as tape:
            outputs = self._model_action(state, training=True)
            log_probs = [
                tf.math.log(output[0, sampled_actions[i]]) for i, output in enumerate(outputs)
            ]
            actor_loss = -tf.reduce_sum(log_probs) * advantage

        grads = tape.gradient(actor_loss, self._model_action.trainable_variables)
        if grads is not None and all(g is not None for g in grads):
            self._model_action.optimizer.apply_gradients(
                zip(grads, self._model_action.trainable_variables)
            )
        else:
            logging.warning("Gradient cannot be calculated: %s", grads)

        return actor_loss.numpy(), critic_loss

    def predict(self, state: list[int]):
        return self._choose_action(state)

    def save_model(self, location: Path):
        pass

    def predict_reward(self, state, action) -> Optional[int]:
        if not self._model_action or not self._model_critic:
            logging.error("One of the models is missing")
            return None

        state = np.expand_dims(state, axis=0)
        if isinstance(action, list):
            action_one_hot = []
            for act_set in action:
                for i, act in enumerate(act_set):
                    max_value = max(act)
                    for i in range(len(act)):
                        if act[i] == max_value:
                            action_one_hot.append(i + 1)
        elif isinstance(action, np.ndarray):
            action_one_hot = []
            for i, act in enumerate(action):
                max_value = max(act)
                for i in range(len(act)):
                    if act[i] == max_value:
                        action_one_hot.append(i + 1)
        else:
            raise NotImplementedError
        action_one_hot = np.expand_dims(action_one_hot, axis=0)

        predicted_reward = self._model_critic.predict([state, action_one_hot])

        return predicted_reward
