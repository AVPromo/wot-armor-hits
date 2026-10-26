# -*- coding: utf-8 -*-
"""View model of the settings menu of the hits screen: its title, the mod's settings, each on or off, and how the
battles of each group of modes are kept."""
from frameworks.wulf import Array, ViewModel


class SettingItemModel(ViewModel):
    # A setting: its key in the settings file, its label, a note under it ('' for none) and whether it is on.
    __slots__ = ()

    def __init__(self, properties=4, commands=0):
        super(SettingItemModel, self).__init__(properties=properties, commands=commands)

    def getKey(self):
        return self._getString(0)

    def setKey(self, value):
        self._setString(0, value)

    def getLabel(self):
        return self._getString(1)

    def setLabel(self, value):
        self._setString(1, value)

    def getNote(self):
        return self._getString(2)

    def setNote(self, value):
        self._setString(2, value)

    def getIsOn(self):
        return self._getBool(3)

    def setIsOn(self, value):
        self._setBool(3, value)

    def _initialize(self):
        super(SettingItemModel, self)._initialize()
        self._addStringProperty('key', '')
        self._addStringProperty('label', '')
        self._addStringProperty('note', '')
        self._addBoolProperty('isOn', False)


class BattleModeModel(ViewModel):
    # A group of modes (data/battle_modes.py): its key, its label and how its battles are kept (off, session, file).
    __slots__ = ()

    def __init__(self, properties=3, commands=0):
        super(BattleModeModel, self).__init__(properties=properties, commands=commands)

    def getGroup(self):
        return self._getString(0)

    def setGroup(self, value):
        self._setString(0, value)

    def getLabel(self):
        return self._getString(1)

    def setLabel(self, value):
        self._setString(1, value)

    def getSaving(self):
        return self._getString(2)

    def setSaving(self, value):
        self._setString(2, value)

    def _initialize(self):
        super(BattleModeModel, self)._initialize()
        self._addStringProperty('group', '')
        self._addStringProperty('label', '')
        self._addStringProperty('saving', '')


class SettingsMenuModel(ViewModel):
    __slots__ = ('onToggle', 'onBattleMode')

    def __init__(self, properties=7, commands=2):
        super(SettingsMenuModel, self).__init__(properties=properties, commands=commands)

    def getTitle(self):
        return self._getString(0)

    def setTitle(self, value):
        self._setString(0, value)

    def getItems(self):
        return self._getArray(1)

    def setItems(self, value):
        self._setArray(1, value)

    @staticmethod
    def getItemsType():
        return SettingItemModel

    def getModesTitle(self):
        return self._getString(2)

    def setModesTitle(self, value):
        self._setString(2, value)

    def getModes(self):
        return self._getArray(3)

    def setModes(self, value):
        self._setArray(3, value)

    @staticmethod
    def getModesType():
        return BattleModeModel

    def getOffLabel(self):
        return self._getString(4)

    def setOffLabel(self, value):
        self._setString(4, value)

    def getSessionLabel(self):
        return self._getString(5)

    def setSessionLabel(self, value):
        self._setString(5, value)

    def getFileLabel(self):
        return self._getString(6)

    def setFileLabel(self, value):
        self._setString(6, value)

    def _initialize(self):
        super(SettingsMenuModel, self)._initialize()
        self._addStringProperty('title', '')
        self._addArrayProperty('items', Array())
        self._addStringProperty('modesTitle', '')
        self._addArrayProperty('modes', Array())
        self._addStringProperty('offLabel', '')
        self._addStringProperty('sessionLabel', '')
        self._addStringProperty('fileLabel', '')
        # {key}: the page's click on a setting, which turns it over.
        self.onToggle = self._addCommand('onToggle')
        # {group, saving}: the page's click on how a group's battles are kept.
        self.onBattleMode = self._addCommand('onBattleMode')
