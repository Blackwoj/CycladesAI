from ....abstract_models.AbstractModelClassAC import AbstractModelClassAC


class AresMoveModel(AbstractModelClassAC):

    @property
    def model_name(self) -> str:
        return "AresMoveModel"

    @property
    def action_outputs(self) -> list[int]:
        """Returns number of outputs: 3
        1. source island(1-13)
        2. target island(1-13)
        3. quantity(1-6)
        """
        return [13, 13, 6]

    def get_action(self, state):
        return self.model_name, self._choose_action(state)
