from .common.Config import Config
from .views.MenuView import MenuView
from .views.RollView import RollView

class ViewManager():

    def __init__(self, screen):
        self.screen = screen
        self.menu_view = MenuView(self.screen, Config.app.background_dir / "menu_bg.png")
        self.roll_view = RollView(self.screen, Config.app.background_dir / "roll.png")

    def show_menu(self):
        self.menu_view.render_view()
        pass

    def show_board(self):
        pass

    def show_pause(self):
        pass
    
    def show_roll(self):
        self.roll_view.render_view()
