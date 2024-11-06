from .ares_moves.ares_move_model import AresMoveModel
from .ares_moves.ares_req_model import AresReqModel
from ..common_models.build_model import BuildModel
from pathlib import Path
from ...abstract_models.abstract_decider_model import AbstractDecider


class AresModel(AbstractDecider):

    def __init__(self, build_model: BuildModel) -> None:
        super().__init__(build_model)
        self._move_model = AresMoveModel()
        self._req_model = AresReqModel()

    def load_model(self, location: Path):
        self._move_model.load_model(location)
        self._req_model.load_model(location)
        super().load_model(location)

    @property
    def model_name(self):
        return "AresDeciderModel"
