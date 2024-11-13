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
    RollModel = RollModel()
    MetroCardModel = BuildMetroCardsModel()
    MetroBuildingModel = BuildMetroBuildingModel()
    submodels = [
        AresModel,
        PosejdonModel,
        AtenaModel,
        ZeusModel,
        ApolloModel,
        RollModel,
        MetroBuildingModel,
        MetroCardModel,
        BuildModel
    ]

    @classmethod
    def load_model(cls, path: Path = Config.models_path):
        for model in cls.submodels:
            model.load_model(path)

    @classmethod
    def save_model(cls, path: Path = Config.models_path):
        for model in cls.submodels:
            model.save_model(path)
        pass

    @classmethod
    def predict(cls):
        pass

    @classmethod
    def train_model(cls, path: Path = Config.models_path):
        pass

    @classmethod
    def define_model(cls):
        pass
