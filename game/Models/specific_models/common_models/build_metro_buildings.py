from ...abstract_models.abstract_base_model import AbstractModelClass


class BuildMetroBuildingModel(AbstractModelClass):

    @property
    def model_name(self) -> str:
        return "BuildMetroBuildingsModel"

    @property
    def action_outputs(self) -> list[int]:
        """Returns number of outputs: 1
        1. Island place target: (1-13)
        2.1. Ares building island (1-13)
        2.2. Ares building place (1-4)
        3.1. Posejdon building island
        3.2. Posejdon building place
        4.1. Atena building island
        4.2. Atena building place
        5.1. Zeus building island
        5.2. Zeus building place
        """
        return [
            13,
            13, 4,
            13, 4,
            13, 4,
            13, 4
        ]
