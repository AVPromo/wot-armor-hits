# -*- coding: utf-8 -*-
"""Scene panel of the hits screen, at the bottom: which hit lines the scene draws and the shooter view.

ScenePanelPresenter fills the view model (views/models/scene_panel_model.py) and keeps the choices: the lines of all
the hits the hits panel shows or of the chosen hit only (allLines), and the shooter view, the camera looking along
the chosen hit's shell (shooterView). It tells its listeners when they change (onChanged); the hit lines presenter
draws by them. The "All" label is the client's text, the others the mod's.
"""
from Event import Event

from gui.mods.sagtary_armor_hits.data.client_names import clientText

_ALL_KEY = '#menu:carousel_tank_filter/all'


class ScenePanelPresenter(object):

    def __init__(self, model, texts):
        # texts: {'lines', 'current', 'shooter'} in the client language.
        self._model = model
        self._texts = texts
        self.allLines = False
        self.shooterView = False
        self.onChanged = Event()

    def init(self):
        with self._model.transaction() as model:
            model.setLinesLabel(self._texts['lines'])
            model.setAllLabel(clientText(_ALL_KEY) or '')
            model.setCurrentLabel(self._texts['current'])
            model.setShooterLabel(self._texts['shooter'])
        self._model.onLines += self._onLines
        self._model.onShooterView += self._onShooterView
        self._update()

    def fini(self):
        self._model.onShooterView -= self._onShooterView
        self._model.onLines -= self._onLines
        self.onChanged.clear()
        self._model = None

    def _onLines(self, args=None):
        allLines = bool((args or {}).get('all'))
        if allLines != self.allLines:
            self.allLines = allLines
            self._update()
            self.onChanged()

    def _onShooterView(self, args=None):
        self.shooterView = not self.shooterView
        self._update()
        self.onChanged()

    def _update(self):
        with self._model.transaction() as model:
            model.setAllLines(self.allLines)
            model.setShooterView(self.shooterView)
