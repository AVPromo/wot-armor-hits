# -*- coding: utf-8 -*-
"""View models of the overlay panel of the hits screen: the overlay type, like on the client's armor page. Written like
the client's generated view models (typed getters and setters by property index).
"""
from frameworks.wulf import Array, ViewModel


class OverlayItemModel(ViewModel):
    # An overlay type of the dropdown: its id and its name.
    __slots__ = ()

    def __init__(self, properties=2, commands=0):
        super(OverlayItemModel, self).__init__(properties=properties, commands=commands)

    def getId(self):
        return self._getString(0)

    def setId(self, value):
        self._setString(0, value)

    def getLabel(self):
        return self._getString(1)

    def setLabel(self, value):
        self._setString(1, value)

    def _initialize(self):
        super(OverlayItemModel, self)._initialize()
        self._addStringProperty('id', '')
        self._addStringProperty('label', '')


class OverlayPanelModel(ViewModel):
    __slots__ = ('onSelect',)

    def __init__(self, properties=3, commands=1):
        super(OverlayPanelModel, self).__init__(properties=properties, commands=commands)

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
        return OverlayItemModel

    def getSelectedId(self):
        return self._getString(2)

    def setSelectedId(self, value):
        self._setString(2, value)

    def _initialize(self):
        super(OverlayPanelModel, self)._initialize()
        self._addStringProperty('title', '')
        self._addArrayProperty('items', Array())
        self._addStringProperty('selectedId', '')
        # {id}: the overlay type chosen in the dropdown.
        self.onSelect = self._addCommand('onSelect')
