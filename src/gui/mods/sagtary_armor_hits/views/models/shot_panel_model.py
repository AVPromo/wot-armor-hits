# -*- coding: utf-8 -*-
"""View models of the shot panel of the hits screen: the chosen hit's shooter and target, its result and its numbers
in sections. Written like the client's generated view models (typed getters and setters by property index).
"""
from frameworks.wulf import Array, ViewModel


class ShotModuleModel(ViewModel):
    # A module or a shell of a vehicle card: the client's icon, the module's tier ('' for a shell), its name.
    __slots__ = ()

    def __init__(self, properties=3, commands=0):
        super(ShotModuleModel, self).__init__(properties=properties, commands=commands)

    def getIcon(self):
        return self._getString(0)

    def setIcon(self, value):
        self._setString(0, value)

    def getTier(self):
        return self._getString(1)

    def setTier(self, value):
        self._setString(1, value)

    def getLabel(self):
        return self._getString(2)

    def setLabel(self, value):
        self._setString(2, value)

    def _initialize(self):
        super(ShotModuleModel, self)._initialize()
        self._addStringProperty('icon', '')
        self._addStringProperty('tier', '')
        self._addStringProperty('label', '')


class ShotVehicleModel(ViewModel):
    # A vehicle card: its role (shooter, target), the player, the vehicle's name, tier, icon and nation flag, and the
    # modules shown beside it.
    __slots__ = ()

    def __init__(self, properties=7, commands=0):
        super(ShotVehicleModel, self).__init__(properties=properties, commands=commands)

    def getRole(self):
        return self._getString(0)

    def setRole(self, value):
        self._setString(0, value)

    def getPlayer(self):
        return self._getString(1)

    def setPlayer(self, value):
        self._setString(1, value)

    def getVehicleName(self):
        return self._getString(2)

    def setVehicleName(self, value):
        self._setString(2, value)

    def getTier(self):
        return self._getString(3)

    def setTier(self, value):
        self._setString(3, value)

    def getIcon(self):
        return self._getString(4)

    def setIcon(self, value):
        self._setString(4, value)

    def getFlag(self):
        return self._getString(5)

    def setFlag(self, value):
        self._setString(5, value)

    def getModules(self):
        return self._getArray(6)

    def setModules(self, value):
        self._setArray(6, value)

    @staticmethod
    def getModulesType():
        return ShotModuleModel

    def _initialize(self):
        super(ShotVehicleModel, self)._initialize()
        self._addStringProperty('role', '')
        self._addStringProperty('player', '')
        self._addStringProperty('vehicleName', '')
        self._addStringProperty('tier', '')
        self._addStringProperty('icon', '')
        self._addStringProperty('flag', '')
        self._addArrayProperty('modules', Array())


class ShotRowModel(ViewModel):
    # A line of a section: a value, its label, whether the value is counted in the garage (not told by the battle).
    __slots__ = ()

    def __init__(self, properties=3, commands=0):
        super(ShotRowModel, self).__init__(properties=properties, commands=commands)

    def getValue(self):
        return self._getString(0)

    def setValue(self, value):
        self._setString(0, value)

    def getLabel(self):
        return self._getString(1)

    def setLabel(self, value):
        self._setString(1, value)

    def getCounted(self):
        return self._getBool(2)

    def setCounted(self, value):
        self._setBool(2, value)

    def _initialize(self):
        super(ShotRowModel, self)._initialize()
        self._addStringProperty('value', '')
        self._addStringProperty('label', '')
        self._addBoolProperty('counted', False)


class ShotSectionModel(ViewModel):
    # A section: its kind (damage, penetration, armor, angle, distance, crits: the page's icon and accent), title,
    # units, value, whether the value is counted in the garage, and its lines.
    __slots__ = ()

    def __init__(self, properties=6, commands=0):
        super(ShotSectionModel, self).__init__(properties=properties, commands=commands)

    def getKind(self):
        return self._getString(0)

    def setKind(self, value):
        self._setString(0, value)

    def getTitle(self):
        return self._getString(1)

    def setTitle(self, value):
        self._setString(1, value)

    def getUnits(self):
        return self._getString(2)

    def setUnits(self, value):
        self._setString(2, value)

    def getValue(self):
        return self._getString(3)

    def setValue(self, value):
        self._setString(3, value)

    def getCounted(self):
        return self._getBool(4)

    def setCounted(self, value):
        self._setBool(4, value)

    def getRows(self):
        return self._getArray(5)

    def setRows(self, value):
        self._setArray(5, value)

    @staticmethod
    def getRowsType():
        return ShotRowModel

    def _initialize(self):
        super(ShotSectionModel, self)._initialize()
        self._addStringProperty('kind', '')
        self._addStringProperty('title', '')
        self._addStringProperty('units', '')
        self._addStringProperty('value', '')
        self._addBoolProperty('counted', False)
        self._addArrayProperty('rows', Array())


class ShotPanelModel(ViewModel):
    __slots__ = ()

    def __init__(self, properties=6, commands=0):
        super(ShotPanelModel, self).__init__(properties=properties, commands=commands)

    def getIsVisible(self):
        return self._getBool(0)

    def setIsVisible(self, value):
        self._setBool(0, value)

    @property
    def shooter(self):
        return self._getViewModel(1)

    @staticmethod
    def getShooterType():
        return ShotVehicleModel

    @property
    def target(self):
        return self._getViewModel(2)

    @staticmethod
    def getTargetType():
        return ShotVehicleModel

    def getResultIcon(self):
        # The hit icon class of the hits panel: result and side, 'damage__received'.
        return self._getString(3)

    def setResultIcon(self, value):
        self._setString(3, value)

    def getNumber(self):
        # '#4 · 3:11': the hit's number in the list and its battle time.
        return self._getString(4)

    def setNumber(self, value):
        self._setString(4, value)

    def getSections(self):
        return self._getArray(5)

    def setSections(self, value):
        self._setArray(5, value)

    @staticmethod
    def getSectionsType():
        return ShotSectionModel

    def _initialize(self):
        super(ShotPanelModel, self)._initialize()
        self._addBoolProperty('isVisible', False)
        self._addViewModelProperty('shooter', ShotVehicleModel())
        self._addViewModelProperty('target', ShotVehicleModel())
        self._addStringProperty('resultIcon', '')
        self._addStringProperty('number', '')
        self._addArrayProperty('sections', Array())
