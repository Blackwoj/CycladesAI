from ..abstract_models.abstract_base_model import AbstractModelClass


class ApolloModel(AbstractModelClass):

    @property
    def model_name(self) -> str:
        return "ApolloModel"

    @property
    def action_outputs(self) -> list[int]:
        """Returns number of outputs: 1
        2. target island (1-13 )
        """
        return [13]
