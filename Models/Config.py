from pathlib import Path


class Config:

    model_extension = ".h5"
    config_path = Path(__file__).resolve()
    builded_models_folder = "Models_Builded"
    models_path = config_path.parent.parent / builded_models_folder
