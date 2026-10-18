# -*- coding: utf-8 -*-
"""View model of the hits screen: the battle selector, the hits panel, the developer tools, the overlay panel, the
scene panel, and the commands of the mouse over the 3D scene.
"""
from frameworks.wulf import ViewModel

from gui.mods.sagtary_armor_hits.views.models.battle_selector_model import BattleSelectorModel
from gui.mods.sagtary_armor_hits.views.models.dev_tools_model import DevToolsModel
from gui.mods.sagtary_armor_hits.views.models.hits_panel_model import HitsPanelModel
from gui.mods.sagtary_armor_hits.views.models.overlay_panel_model import OverlayPanelModel
from gui.mods.sagtary_armor_hits.views.models.scene_panel_model import ScenePanelModel


class HitsViewModel(ViewModel):

    def __init__(self, properties=5, commands=2):
        super(HitsViewModel, self).__init__(properties=properties, commands=commands)

    @property
    def battleSelector(self):
        return self._getViewModel(0)

    @staticmethod
    def getBattleSelectorType():
        return BattleSelectorModel

    @property
    def devTools(self):
        return self._getViewModel(1)

    @staticmethod
    def getDevToolsType():
        return DevToolsModel

    @property
    def hitsPanel(self):
        return self._getViewModel(2)

    @staticmethod
    def getHitsPanelType():
        return HitsPanelModel

    @property
    def overlayPanel(self):
        return self._getViewModel(3)

    @staticmethod
    def getOverlayPanelType():
        return OverlayPanelModel

    @property
    def scenePanel(self):
        return self._getViewModel(4)

    @staticmethod
    def getScenePanelType():
        return ScenePanelModel

    def _initialize(self):
        super(HitsViewModel, self)._initialize()
        self._addViewModelProperty('battleSelector', BattleSelectorModel())
        self._addViewModelProperty('devTools', DevToolsModel())
        self._addViewModelProperty('hitsPanel', HitsPanelModel())
        self._addViewModelProperty('overlayPanel', OverlayPanelModel())
        self._addViewModelProperty('scenePanel', ScenePanelModel())
        # Mouse over the scene, from the page: {dx, dy, dz} of a drag or the wheel, {isOver3dScene}.
        self.onMoveSpace = self._addCommand('onMoveSpace')
        self.onMouseOver3dScene = self._addCommand('onMouseOver3dScene')
