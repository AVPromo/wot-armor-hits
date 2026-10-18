# -*- coding: utf-8 -*-
"""View models of the battle selector, written like the client's generated view models (typed getters and setters by
property index). A new field is a new property at the end of _initialize, with its getter and setter.
"""
from frameworks.wulf import Array, ViewModel


class BattleItemModel(ViewModel):
    __slots__ = ()

    def __init__(self, properties=7, commands=0):
        super(BattleItemModel, self).__init__(properties=properties, commands=commands)

    def getId(self):
        return self._getString(0)

    def setId(self, value):
        self._setString(0, value)

    def getMapName(self):
        return self._getString(1)

    def setMapName(self, value):
        self._setString(1, value)

    def getMapImage(self):
        return self._getString(2)

    def setMapImage(self, value):
        self._setString(2, value)

    def getMode(self):
        return self._getString(3)

    def setMode(self, value):
        self._setString(3, value)

    def getVehicleName(self):
        return self._getString(4)

    def setVehicleName(self, value):
        self._setString(4, value)

    def getDate(self):
        return self._getString(5)

    def setDate(self, value):
        self._setString(5, value)

    def getTime(self):
        return self._getString(6)

    def setTime(self, value):
        self._setString(6, value)

    def _initialize(self):
        super(BattleItemModel, self)._initialize()
        self._addStringProperty('id', '')
        self._addStringProperty('mapName', '')
        self._addStringProperty('mapImage', '')
        self._addStringProperty('mode', '')
        self._addStringProperty('vehicleName', '')
        self._addStringProperty('date', '')
        self._addStringProperty('time', '')


class BattleSelectorModel(ViewModel):
    __slots__ = ('onSelect',)

    def __init__(self, properties=4, commands=1):
        super(BattleSelectorModel, self).__init__(properties=properties, commands=commands)

    def getBattles(self):
        return self._getArray(0)

    def setBattles(self, value):
        self._setArray(0, value)

    @staticmethod
    def getBattlesType():
        return BattleItemModel

    def getSelectedId(self):
        return self._getString(1)

    def setSelectedId(self, value):
        self._setString(1, value)

    def getEmptyTitle(self):
        return self._getString(2)

    def setEmptyTitle(self, value):
        self._setString(2, value)

    def getListTitle(self):
        return self._getString(3)

    def setListTitle(self, value):
        self._setString(3, value)

    def _initialize(self):
        super(BattleSelectorModel, self)._initialize()
        self._addArrayProperty('battles', Array())
        self._addStringProperty('selectedId', '')
        self._addStringProperty('emptyTitle', '')
        self._addStringProperty('listTitle', '')
        # {id}: the battle the player picked in the list.
        self.onSelect = self._addCommand('onSelect')
