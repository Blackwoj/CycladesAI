from pathlib import Path
import keras
from keras import layers, optimizers, models
from ..Config import Config
from abc import abstractmethod
import numpy as np
import tensorflow as tf
import logging
from typing import Optional, cast


class AbstractModelClass:

    def __init__(self):
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

    @property
    def state_size(self):
        return 300

    def common_input(self):
        return keras.Input(shape=(300,))

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
        state_input = self.common_input
        x = layers.Dense(64, activation="relu")(state_input)
        x = layers.Dense(64, activation="relu")(x)

        outputs = []
        for output_size in self.action_outputs:
            outputs.append(layers.Dense(output_size, activation="softmax")(x))

        actor_model = models.Model(inputs=state_input, outputs=outputs)
        actor_model.compile(optimizer=optimizers.Adam(lr=0.001), loss="categorical_crossentropy")  # type: ignore
        return actor_model

    def build_critic(self):
        state_input = self.common_input
        action_input = layers.Input(shape=(sum(self.action_outputs),))

        x = layers.Concatenate()([state_input, action_input])
        x = layers.Dense(64, activation="relu")(x)
        x = layers.Dense(64, activation="relu")(x)
        value_output = layers.Dense(1, activation="linear")(x)

        critic_model = models.Model(inputs=[state_input, action_input], outputs=value_output)
        critic_model.compile(optimizer=optimizers.Adam(lr=0.001), loss="mse")  # type: ignore
        return critic_model

    @abstractmethod
    def get_action(self):
        raise NotImplementedError

    def _choose_action(self, state):
        state = np.expand_dims(state, axis=0)
        if self._model_action is None:
            logging.error("No action model for %s", self.model_name)
            self._model_action = self.build_actor()

        predictions = self._model_action.predict(state)

        action = []
        for i, output in enumerate(predictions):
            action.append(np.random.choice(range(self.action_outputs[i]), p=output[0]))

        return action

    def train(self, state, action, reward, next_state, gamma=0.99):
        if not self._model_action:
            return
        state = np.expand_dims(state, axis=0)
        next_state = np.expand_dims(next_state, axis=0)

        action_one_hot = np.zeros(sum(self.action_outputs))
        action_index = 0
        for i, act in enumerate(action):
            action_one_hot[action_index + act] = 1
            action_index += self.action_outputs[i]
        if self._model_critic is not models.Model:
            logging.error("No action model for %s", self.model_name)
            return None

        value = self._model_critic.predict([state, np.expand_dims(action_one_hot, axis=0)])
        next_value = self._model_critic.predict([next_state, np.expand_dims(action_one_hot, axis=0)])
        target_value = reward + gamma * next_value

        critic_loss = self._model_critic.train_on_batch([state, np.expand_dims(action_one_hot, axis=0)], target_value)

        advantage = target_value - value
        with tf.GradientTape() as tape:
            outputs = self._model_action(state, training=True)
            log_probs = [tf.math.log(output[0, action[i]]) for i, output in enumerate(outputs)]
            actor_loss = -tf.reduce_sum(log_probs) * advantage

        grads = tape.gradient(actor_loss, self._model_action.trainable_variables)

        if grads is not None and all(g is not None for g in grads):
            self._model_action.optimizer.apply_gradients(
                zip(grads, self._model_action.trainable_variables)
            )
        else:
            logging.warning("Gradient cannot be calculated: %s", grads)

        return actor_loss.numpy(), critic_loss

    def predict(self, state):
        return self._choose_action(state)

    def save_model(self, location: Path):
        pass
