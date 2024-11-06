from pathlib import Path
from .specific_models.ares_models.ares_decider import AresModel
from .specific_models.posejdon_models.posejdon_decider import PosejdonModel
from .specific_models.atena_model import AtenaModel
from .specific_models.zeus_model import ZeusModel
from .specific_models.apollo_model import ApolloModel


class CycladesAI:
    model = None
    AresModel = AresModel()
    PosejdonModel = PosejdonModel()
    AtenaModel = AtenaModel()
    ZeusModel = ZeusModel()
    ApolloModel = ApolloModel()

    @classmethod
    def load_model(cls, path: Path):
        pass

    @classmethod
    def save_model(cls, path: Path):
        pass

    @classmethod
    def predict(cls):
        pass
        
    @classmethod
    def train_model(cls, path: Path):
        
    @classmethod
    def define_model(cls):
        pass