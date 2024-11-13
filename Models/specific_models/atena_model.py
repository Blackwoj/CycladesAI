from ..abstract_models.abstract_decider_model import AbstractDecider
from .common_models.build_model import BuildModel


class AtenaModel(AbstractDecider):

    def __init__(self, build_model: BuildModel) -> None:
        super().__init__(build_model)

    @property
    def model_name(self) -> str:
        return "AtenaDeciderModel"

    @property
    def action_outputs(self) -> list[int]:
        """Returns number of outputs
        1. Buy Card(0 - 1)
        3. BuildBuilding(0 - 1)
        4. End Round(0 - 1)
        """
        return [1, 1, 1]
