from ..abstract_models.AbstractModelClassAC import AbstractModelClassAC


class ApolloModel(AbstractModelClassAC):

    @property
    def model_name(self) -> str:
        return "ApolloModel"

    @property
    def action_outputs(self) -> list[int]:
        """Returns number of outputs: 1
        2. target island (1-13 )
        """
        return [13]

    def get_action(self, state):
        return self._choose_action(state)
