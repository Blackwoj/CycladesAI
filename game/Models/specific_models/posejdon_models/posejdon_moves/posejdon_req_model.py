from ....abstract_models.AbstractModelClassAC import AbstractModelClassAC


class PosejdonReqModel(AbstractModelClassAC):

    @property
    def model_name(self):
        return "PosejdonReqModel"

    @property
    def action_outputs(self) -> list[int]:
        """Returns number of outputs: 1
        1. target water
        """

        return [61]

    def get_action(self, state):
        return self.model_name, self._choose_action(state)
