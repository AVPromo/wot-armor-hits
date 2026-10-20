# -*- coding: utf-8 -*-
"""View model of the scene panel of the hits screen, at the bottom: which hit lines are drawn (all the shown hits or
the chosen one) and the shooter view (the camera looks along the chosen hit's shell).
"""
from frameworks.wulf import ViewModel


class ScenePanelModel(ViewModel):
    __slots__ = ('onLines', 'onShooterView')

    def __init__(self, properties=6, commands=2):
        super(ScenePanelModel, self).__init__(properties=properties, commands=commands)

    def getAllLabel(self):
        return self._getString(0)

    def setAllLabel(self, value):
        self._setString(0, value)

    def getCurrentLabel(self):
        return self._getString(1)

    def setCurrentLabel(self, value):
        self._setString(1, value)

    def getShooterLabel(self):
        return self._getString(2)

    def setShooterLabel(self, value):
        self._setString(2, value)

    def getAllLines(self):
        # The lines of all the shown hits, else of the chosen hit only.
        return self._getBool(3)

    def setAllLines(self, value):
        self._setBool(3, value)

    def getShooterView(self):
        return self._getBool(4)

    def setShooterView(self, value):
        self._setBool(4, value)

    def getAllLinesEnabled(self):
        # "All" can be chosen: on the received side only.
        return self._getBool(5)

    def setAllLinesEnabled(self, value):
        self._setBool(5, value)

    def _initialize(self):
        super(ScenePanelModel, self)._initialize()
        self._addStringProperty('allLabel', '')
        self._addStringProperty('currentLabel', '')
        self._addStringProperty('shooterLabel', '')
        self._addBoolProperty('allLines', False)
        self._addBoolProperty('shooterView', False)
        self._addBoolProperty('allLinesEnabled', True)
        # {all}: all the shown hits' lines or the chosen one's; the shooter view on or off.
        self.onLines = self._addCommand('onLines')
        self.onShooterView = self._addCommand('onShooterView')
