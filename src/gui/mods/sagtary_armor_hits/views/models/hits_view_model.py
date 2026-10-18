# -*- coding: utf-8 -*-
"""View model of the hits screen: the battle selector, and the commands of the mouse over the 3D scene."""
from frameworks.wulf import ViewModel

from gui.mods.sagtary_armor_hits.views.models.battle_selector_model import BattleSelectorModel


class HitsViewModel(ViewModel):

    def __init__(self, properties=1, commands=2):
        super(HitsViewModel, self).__init__(properties=properties, commands=commands)

    @property
    def battleSelector(self):
        return self._getViewModel(0)

    @staticmethod
    def getBattleSelectorType():
        return BattleSelectorModel

    def _initialize(self):
        super(HitsViewModel, self)._initialize()
        self._addViewModelProperty('battleSelector', BattleSelectorModel())
        # Mouse over the scene, from the page: {dx, dy, dz} of a drag or the wheel, {isOver3dScene}.
        self.onMoveSpace = self._addCommand('onMoveSpace')
        self.onMouseOver3dScene = self._addCommand('onMouseOver3dScene')
