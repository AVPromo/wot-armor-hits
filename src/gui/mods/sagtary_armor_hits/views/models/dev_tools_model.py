# -*- coding: utf-8 -*-
"""View model of the developer tools of the hits screen: the Import and Export buttons of the battles file."""
from frameworks.wulf import ViewModel


class DevToolsModel(ViewModel):
    __slots__ = ('onImport', 'onExport')

    def __init__(self, properties=3, commands=2):
        super(DevToolsModel, self).__init__(properties=properties, commands=commands)

    def getIsVisible(self):
        return self._getBool(0)

    def setIsVisible(self, value):
        self._setBool(0, value)

    def getImportLabel(self):
        return self._getString(1)

    def setImportLabel(self, value):
        self._setString(1, value)

    def getExportLabel(self):
        return self._getString(2)

    def setExportLabel(self, value):
        self._setString(2, value)

    def _initialize(self):
        super(DevToolsModel, self)._initialize()
        self._addBoolProperty('isVisible', False)
        self._addStringProperty('importLabel', '')
        self._addStringProperty('exportLabel', '')
        self.onImport = self._addCommand('onImport')
        self.onExport = self._addCommand('onExport')
