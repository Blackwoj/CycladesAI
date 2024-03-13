from pygame import Surface
from .AbstractView import AbstractView
from pathlib import Path

class BoardView(AbstractView):

    def __init__(self, screen: Surface, background: Path):
        super().__init__(screen, background)

    def render_view(self):
        self.scale_background(self._background)
