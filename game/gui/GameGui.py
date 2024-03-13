from .common.Config import Config
from .views.MenuView import MenuView


class ViewManager():

    def __init__(self, screen):
        self.screen = screen
        self.menu_view = MenuView(self.screen, Config.app.background_dir)

    def show_menu(self):
        self.menu_view.render_view()
        pass

    def show_board(self):
        pass

    def show_pause(self):
        pass
