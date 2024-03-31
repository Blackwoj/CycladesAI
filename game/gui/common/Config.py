from .config_section.AppSection import AppSection
from .config_section.Locations import Locations
from .config_section.BoardConfig import BoardConfig


class Config():

    app: AppSection = AppSection()
    locations: Locations = Locations()
    boards: BoardConfig = BoardConfig()
