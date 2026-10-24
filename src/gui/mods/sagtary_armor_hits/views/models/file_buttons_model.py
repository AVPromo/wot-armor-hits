# -*- coding: utf-8 -*-
"""View model of the file buttons of the hits screen: save the chosen battle to its file (an icon and a label), delete
all the battles (an icon and a label; the page asks first: the question, delete, cancel)."""
from frameworks.wulf import ViewModel


class FileButtonsModel(ViewModel):
    __slots__ = ('onSave', 'onDelete')

    def __init__(self, properties=7, commands=2):
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

    def getCanDelete(self):
        # There are battles.
        return self._getBool(2)

    def setCanDelete(self, value):
        self._setBool(2, value)

    def getDeleteLabel(self):
        return self._getString(3)

    def setDeleteLabel(self, value):
        self._setString(3, value)

    def getConfirmText(self):
        # The question before the delete, and the labels of its two choices.
        return self._getString(4)

    def setConfirmText(self, value):
        self._setString(4, value)

    def getConfirmLabel(self):
        return self._getString(5)

    def setConfirmLabel(self, value):
        self._setString(5, value)

    def getCancelLabel(self):
        return self._getString(6)

    def setCancelLabel(self, value):
        self._setString(6, value)

    def _initialize(self):
        super(FileButtonsModel, self)._initialize()
        self._addBoolProperty('canSave', False)
        self._addStringProperty('saveLabel', '')
        self._addBoolProperty('canDelete', False)
        self._addStringProperty('deleteLabel', '')
        self._addStringProperty('confirmText', '')
        self._addStringProperty('confirmLabel', '')
        self._addStringProperty('cancelLabel', '')
        self.onSave = self._addCommand('onSave')
        self.onDelete = self._addCommand('onDelete')
