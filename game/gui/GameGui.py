from .views.MenuView import MenuView
from .common.Config import Config

class ViewManager():

    def __init__(self, screen):
        self.screen = screen
        self.menu_view = MenuView(self.screen, Config.app.background_dir)

    def show_menu(self):
        self.menu_view.render_view()
        pass

    def show_gameboard(self):
        pass

    def show_pause(self):
        pass
