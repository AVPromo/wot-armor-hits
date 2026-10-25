# -*- coding: utf-8 -*-
"""View model of the scene panel of the hits screen, at the bottom: which hit lines are drawn (all the shown hits or
the chosen one), the shooter view (the camera looks along the chosen hit's shell) and the camera reset; the lines and
the camera are groups under their titles.
"""
from frameworks.wulf import ViewModel


class ScenePanelModel(ViewModel):
    __slots__ = ('onLines', 'onShooterView', 'onResetCamera')

    def __init__(self, properties=8, commands=3):
        super(ScenePanelModel, self).__init__(properties=properties, commands=commands)

    def getLinesTitle(self):
        return self._getString(0)

    def setLinesTitle(self, value):
        self._setString(0, value)

    def getAllLabel(self):
        # The check box of the lines of all the shown hits.
        return self._getString(1)

    def setAllLabel(self, value):
        self._setString(1, value)

    def getShooterLabel(self):
        return self._getString(2)

    def setShooterLabel(self, value):
        self._setString(2, value)

    def getAllLines(self):
        # The lines of all the shown hits are drawn, not only the chosen hit's.
        return self._getBool(3)

    def setAllLines(self, value):
        self._setBool(3, value)

    def getShooterView(self):
        return self._getBool(4)

    def setShooterView(self, value):
        self._setBool(4, value)

    def getAllLinesEnabled(self):
        # False on the dealt side: only the chosen hit's line, the lines group hidden.
        return self._getBool(5)

    def setAllLinesEnabled(self, value):
        self._setBool(5, value)

    def getResetLabel(self):
        return self._getString(6)

    def setResetLabel(self, value):
        self._setString(6, value)

    def getCameraTitle(self):
        return self._getString(7)

    def setCameraTitle(self, value):
        self._setString(7, value)

    def _initialize(self):
        super(ScenePanelModel, self)._initialize()
        self._addStringProperty('linesTitle', '')
        self._addStringProperty('allLabel', '')
        self._addStringProperty('shooterLabel', '')
        self._addBoolProperty('allLines', False)
        self._addBoolProperty('shooterView', False)
        self._addBoolProperty('allLinesEnabled', True)
        self._addStringProperty('resetLabel', '')
        self._addStringProperty('cameraTitle', '')
        # onLines: {'all': bool}.
        self.onLines = self._addCommand('onLines')
        self.onShooterView = self._addCommand('onShooterView')
        self.onResetCamera = self._addCommand('onResetCamera')
