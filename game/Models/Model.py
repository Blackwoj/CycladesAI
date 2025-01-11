from pathlib import Path
from .specific_models.ares_models.ares_decider import AresModel
from .specific_models.posejdon_models.posejdon_decider import PosejdonModel
from .specific_models.atena_model import AtenaModel
from .specific_models.zeus_model import ZeusModel
from .specific_models.apollo_model import ApolloModel
from .specific_models.roll_model import RollModel
from .specific_models.common_models.build_model import BuildModel
from .specific_models.common_models.build_metro_buildings import BuildMetroBuildingModel
from .specific_models.common_models.build_metro_cards import BuildMetroCardsModel
from .Config import Config


class CycladesAI:
    model = None
    BuildModel = BuildModel()
    AresModel = AresModel(BuildModel)
    PosejdonModel = PosejdonModel(BuildModel)
    AtenaModel = AtenaModel(BuildModel)
    ZeusModel = ZeusModel(BuildModel)
    ApolloModel = ApolloModel()
    RollModel = RollModel(
        {
            "ares": AresModel,
            "posejdon": PosejdonModel,
            "atena": AtenaModel,
            "zeus": ZeusModel,
            "apollon": ApolloModel
        }
    )
    MetroCardModel = BuildMetroCardsModel()
    MetroBuildingModel = BuildMetroBuildingModel()
    submodels = [
        AresModel,
        PosejdonModel,
        AtenaModel,
        ZeusModel,
        ApolloModel,
        MetroBuildingModel,
        MetroCardModel,
        BuildModel
    ]

    def load_model(self, path: Path = Config.models_path):
        for model in self.submodels:
            model.load_model(path)

    def save_model(self, path: Path = Config.models_path):
        for model in self.submodels:
            model.save_model(path)
        pass

    def predict(
        self,
        state: list[int],
        bids
    ):
        for key in bids.keys():
            bids[key][1] += 1
        pass

    def train_model(
        self,
        state: list[int],
        next_state: list[int],
        reward: int,
        output: list[int],
        stage,
        extras
    ):
        if stage == "roll":
            pass
        elif stage == "board":
            pass
        pass
