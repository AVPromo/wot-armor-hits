# -*- coding: utf-8 -*-
"""Names and classes of vehicles and names of maps by their ids, read from the client's caches, and texts of the
client, in the client language.

A Battle keeps only the ids (vehicleId, mapId), so a battle read from a file is shown in the current client language.
None when the client does not have the vehicle or the map (removed in an update).
"""
import logging

import ArenaType
from helpers import i18n
from items import vehicles

_logger = logging.getLogger('sagtary.armor_hits')


# The maps training dummies ('ussr:R72_T150_MapsTraining_Dummy_HT_2') are named by their class only ("Heavy Tank");
# the vehicle they copy ('ussr:R72_T150') has the name.
_MAPS_TRAINING_MARK = '_MapsTraining_'


def _shownVehicleType(vehicleId):
    # The vehicle type of the vehicle (intCD) to show: the copied vehicle for a maps training dummy.
    vehicleType = vehicles.getVehicleType(vehicleId)
    if _MAPS_TRAINING_MARK in vehicleType.name:
        try:
            nationID, typeID = vehicles.g_list.getIDsByName(vehicleType.name.split(_MAPS_TRAINING_MARK)[0])
            vehicleType = vehicles.g_cache.vehicle(nationID, typeID)
        except Exception:
            _logger.debug('client names: no vehicle copied by %s', vehicleType.name)
    return vehicleType


def vehicleShortName(vehicleId):
    # The short name of the vehicle (intCD), or None.
    if not vehicleId:
        return None
    try:
        return _shownVehicleType(vehicleId).shortUserString
    except Exception:
        _logger.debug('client names: no vehicle %s', vehicleId)
        return None


def shownVehicleId(vehicleId):
    # The intCD of the vehicle to show in the hangar for the vehicle (intCD), or None: the copied vehicle for a maps
    # training dummy.
    if not vehicleId:
        return None
    try:
        return _shownVehicleType(vehicleId).compactDescr
    except Exception:
        _logger.debug('client names: no vehicle %s', vehicleId)
        return None


def mapNames(mapId):
    # (map name, map folder name) of the map (geometryID), or None. The folder names the map images.
    if not mapId or mapId not in ArenaType.g_geometryCache:
        return None
    try:
        geometry = ArenaType.g_geometryCache[mapId]
        return i18n.makeString(geometry.name), geometry.geometryName
    except Exception:
        _logger.debug('client names: no map %s', mapId)
        return None


def vehicleClass(vehicleId):
    # The vehicle class tag ('lightTank', 'mediumTank', 'heavyTank', 'AT-SPG', 'SPG'), or None.
    if not vehicleId:
        return None
    try:
        return vehicles.getVehicleClass(vehicleId)
    except Exception:
        _logger.debug('client names: no vehicle %s', vehicleId)
        return None


def clientText(key):
    # The client's translation of a '#file:key' text, or None when the client does not have it.
    text = i18n.makeString(key)
    return text if text and text != key else None
