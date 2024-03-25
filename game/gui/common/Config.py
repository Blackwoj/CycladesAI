from .config_section.AppSection import AppSection
from .config_section.Locations import Locations


class Config():

    app: AppSection = AppSection()
    locations: Locations = Locations()
