# -*- coding: utf-8 -*-
"""View models of the overlay panel of the hits screen: the overlay type, like on the client's armor page, and the
scales of the chosen overlay. Written like the client's generated view models (typed getters and setters by property
index).
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


class OverlayScaleModel(ViewModel):
    # A scale of the overlay: its title and units, the client's gradient image, the values at its ends.
    __slots__ = ()

    def __init__(self, properties=5, commands=0):
        super(OverlayScaleModel, self).__init__(properties=properties, commands=commands)

    def getTitle(self):
        return self._getString(0)

    def setTitle(self, value):
        self._setString(0, value)

    def getUnits(self):
        return self._getString(1)

    def setUnits(self, value):
        self._setString(1, value)

    def getImage(self):
        return self._getString(2)

    def setImage(self, value):
        self._setString(2, value)

    def getMinValue(self):
        return self._getString(3)

    def setMinValue(self, value):
        self._setString(3, value)

    def getMaxValue(self):
        return self._getString(4)

    def setMaxValue(self, value):
        self._setString(4, value)

    def _initialize(self):
        super(OverlayScaleModel, self)._initialize()
        self._addStringProperty('title', '')
        self._addStringProperty('units', '')
        self._addStringProperty('image', '')
        self._addStringProperty('minValue', '')
        self._addStringProperty('maxValue', '')


class OverlayPanelModel(ViewModel):
    __slots__ = ('onSelect',)

    def __init__(self, properties=4, commands=1):
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

    def getScales(self):
        return self._getArray(3)

    def setScales(self, value):
        self._setArray(3, value)

    @staticmethod
    def getScalesType():
        return OverlayScaleModel

    def _initialize(self):
        super(OverlayPanelModel, self)._initialize()
        self._addStringProperty('title', '')
        self._addArrayProperty('items', Array())
        self._addStringProperty('selectedId', '')
        self._addArrayProperty('scales', Array())
        # {id}: the overlay type chosen in the dropdown.
        self.onSelect = self._addCommand('onSelect')
