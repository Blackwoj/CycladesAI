from ....abstract_models.abstract_base_model import AbstractModelClass


class AresMoveModel(AbstractModelClass):

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
