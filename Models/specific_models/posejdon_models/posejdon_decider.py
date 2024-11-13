from ...abstract_models.abstract_decider_model import AbstractDecider
from .posejdon_moves.posejdon_move_model import PosejdonMoveModel
from .posejdon_moves.posejdon_req_model import PosejdonReqModel
from ..common_models.build_model import BuildModel
from pathlib import Path


class PosejdonModel(AbstractDecider):

    def __init__(self, build_model: BuildModel) -> None:
        super().__init__(build_model)
        self._move_model = PosejdonMoveModel()
        self._req_model = PosejdonReqModel()

    def load_model(self, location: Path):
        self._move_model.load_model(location)
        self._req_model.load_model(location)

    def save_model(self, location: Path):
        self._move_model.save_model(location)
        self._req_model.save_model(location)
        return super().save_model(location)

    @property
    def model_name(self):
        return "PosejdonDeciderModel"

    @property
    def action_outputs(self) -> list[int]:
        """Returns number of outputs
        1. Move entity(0 - 1)
        2. Recruit entity(0 - 1)
        3. Build building(0 - 1)
        4. End Round(0 - 1)
        """
        return [1, 1, 1, 1]
