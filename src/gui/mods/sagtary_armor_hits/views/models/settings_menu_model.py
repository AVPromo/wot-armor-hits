# -*- coding: utf-8 -*-
"""View model of the settings menu of the hits screen: its title and the mod's settings, each on or off."""
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


class SettingsMenuModel(ViewModel):
    __slots__ = ('onToggle',)

    def __init__(self, properties=2, commands=1):
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

    def _initialize(self):
        super(SettingsMenuModel, self)._initialize()
        self._addStringProperty('title', '')
        self._addArrayProperty('items', Array())
        # {key}: the page's click on a setting, which turns it over.
        self.onToggle = self._addCommand('onToggle')
