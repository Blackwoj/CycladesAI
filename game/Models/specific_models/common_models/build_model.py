from ...abstract_models.AbstractModelClassAC import AbstractModelClassAC


class BuildModel(AbstractModelClassAC):

    @property
    def model_name(self) -> str:
        return "BuildModel"

    @property
    def action_outputs(self) -> list[int]:
        """Returns number of outputs: 2
        1. Island place target: (1-13)
        2. Place on island (1-4)
        """
        return [13, 4]

    def get_action(self, state):
        return self.model_name, self._choose_action(state)
