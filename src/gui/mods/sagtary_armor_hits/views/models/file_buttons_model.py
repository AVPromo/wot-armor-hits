# -*- coding: utf-8 -*-
"""View model of the file buttons of the hits screen: save the chosen battle to its file, load the battle files of
the folder (an icon and a label each)."""
from frameworks.wulf import ViewModel


class FileButtonsModel(ViewModel):
    __slots__ = ('onSave', 'onImport')

    def __init__(self, properties=3, commands=2):
        super(FileButtonsModel, self).__init__(properties=properties, commands=commands)

    def getCanSave(self):
        # A battle is chosen.
        return self._getBool(0)

    def setCanSave(self, value):
        self._setBool(0, value)

    def getSaveLabel(self):
        return self._getString(1)

    def setSaveLabel(self, value):
        self._setString(1, value)

    def getImportLabel(self):
        return self._getString(2)

    def setImportLabel(self, value):
        self._setString(2, value)

    def _initialize(self):
        super(FileButtonsModel, self)._initialize()
        self._addBoolProperty('canSave', False)
        self._addStringProperty('saveLabel', '')
        self._addStringProperty('importLabel', '')
        self.onSave = self._addCommand('onSave')
        self.onImport = self._addCommand('onImport')
