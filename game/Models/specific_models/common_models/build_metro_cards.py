from ...abstract_models.AbstractModelClassAC import AbstractModelClassAC


class BuildMetroCardsModel(AbstractModelClassAC):

    @property
    def model_name(self) -> str:
        return "BuildMetroCardsModel"

    @property
    def action_outputs(self) -> list[int]:
        """Returns number of outputs: 1
        1. Island place target: (1-13)
        """
        return [13]
