# -*- coding: utf-8 -*-
"""Hangar vehicle of the hits screen: the vehicle the hits panel shows the hits on.

HangarVehiclePresenter puts the vehicle into the hangar like the client's Vehicle Hub does, as the preview vehicle
(g_currentPreviewVehicle): on the received side the player's vehicle of the battle, on the dealt side the vehicle of
the chosen hit. A battle keeps the vehicle types only, so a vehicle not in the player's garage has its default
modules; a vehicle in the garage is shown as it is there, with its camouflage. When the dealt side has no hits, the
hangar shows no vehicle (HangarSpace.removeVehicle, as the client's vehicle preview does before it loads its own).
When the screen closes, the hangar shows the current vehicle again.
"""
import logging

from CurrentVehicle import g_currentPreviewVehicle, g_currentVehicle
from gui import g_tankActiveCamouflage
from helpers import dependency
from skeletons.gui.shared import IItemsCache
from skeletons.gui.shared.utils import IHangarSpace

from gui.mods.sagtary_armor_hits.data.client_names import shownVehicleId
from gui.mods.sagtary_armor_hits.views.hits.hits_panel import DEALT

_logger = logging.getLogger('sagtary.armor_hits')

# What the presenter shows instead of a vehicle id: no vehicle at all.
_NO_VEHICLE = 'none'


def _vehicleId(battle, side, hit):
    # The intCD of the vehicle the hits are on, _NO_VEHICLE when the dealt side has no hits, None without a battle.
    if battle is None:
        return None
    if side == DEALT:
        if hit is None:
            return _NO_VEHICLE
        return shownVehicleId(hit.vehicleId) or _NO_VEHICLE
    return shownVehicleId(battle.vehicleId)


class HangarVehiclePresenter(object):
    __itemsCache = dependency.descriptor(IItemsCache)
    __hangarSpace = dependency.descriptor(IHangarSpace)

    def __init__(self, hitsPanel):
        self._hitsPanel = hitsPanel
        # What the presenter shows: an intCD, _NO_VEHICLE, or None while the hangar shows the current vehicle.
        self._vehicleId = None

    def init(self):
        self._hitsPanel.onChanged += self._update
        self._update()

    def fini(self):
        self._hitsPanel.onChanged -= self._update
        self._hitsPanel = None
        if self._vehicleId is None:
            return
        self._vehicleId = None
        try:
            if g_currentPreviewVehicle.isPresent():
                g_currentPreviewVehicle.selectNoVehicle()
            else:
                g_currentVehicle.refreshModel()
        except Exception:
            _logger.exception('hangar vehicle: cannot show the current vehicle')

    def _update(self):
        vehicleId = _vehicleId(*self._hitsPanel.selection)
        if vehicleId is None or vehicleId == self._vehicleId:
            return
        _logger.info('hangar vehicle: %s', vehicleId)
        self._vehicleId = vehicleId
        try:
            if vehicleId == _NO_VEHICLE:
                self.__hangarSpace.removeVehicle()
            else:
                self._show(vehicleId)
        except Exception:
            _logger.exception('hangar vehicle: cannot show %s', vehicleId)

    def _show(self, vehicleId):
        # The client's Vehicle Hub (_VehicleHubStatesObserver.__setupPreviewTank); no dark background behind the
        # loading spinner, as the screen stays.
        vehicle = self.__itemsCache.items.getItemByCD(vehicleId)
        strCD, outfit = None, None
        if vehicle.isInInventory:
            season = g_tankActiveCamouflage.get(vehicle.intCD, vehicle.getAnyOutfitSeason())
            strCD, outfit = vehicle.strCD, vehicle.getOutfit(season)
        if g_currentPreviewVehicle.intCD == vehicleId:
            # Still the preview vehicle, its model removed for no hits: the client does not load the same one again.
            self.__hangarSpace.updatePreviewVehicle(g_currentPreviewVehicle.item, outfit, showWaitingBg=False)
        else:
            g_currentPreviewVehicle.selectVehicle(vehicleId, vehicleStrCD=strCD, outfit=outfit, showWaitingBg=False)
