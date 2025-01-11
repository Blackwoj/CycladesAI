from ....abstract_models.AbstractModelClassAC import AbstractModelClassAC


class PosejdonMoveModel(AbstractModelClassAC):

    @property
    def model_name(self) -> str:
        return "PosejdonMoveModel"

    @property
    def action_outputs(self) -> list[int]:
        """Returns number of outputs: 3
        1. source water (1-61)
        2. target water (1-61)
        3. quantity (1-6)
        """
        return [61, 61, 6]

    def get_action(self, state):
        return self.model_name, self._choose_action(state)
