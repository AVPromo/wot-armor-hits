# -*- coding: utf-8 -*-
"""Overlay panel of the hits screen: the overlay of the armor on the hangar vehicle, like on the client's armor page,
and the scales of the chosen overlay.

OverlayPanelPresenter fills the view model (views/models/overlay_panel_model.py) with the client's texts and images
of the armor page (armor_inspector): the overlay types, the scale titles and units, the scale gradients (the color
blind ones with the client's color blind setting). The ends of the armor scales are the hangar vehicle's thickest
main and spaced armor, as the armor page shows them (getMaxArmor), found again when the hangar loads another
vehicle.

The overlay is the client's own, as the armor page shows it: the armor inspector component on the hangar vehicle's
game object (ArmorInspectorComponent; its system colors the armor). It is put on the vehicle when the hangar has
loaded it (HangarSpace.onVehicleChanged) and taken off when the hangar starts to change it, when the overlay is
turned off and when the screen closes. Another type is put on _SHOW_DELAY seconds after the old one is taken off. The penetration chance is the chance of the chosen hit's shell: the gun's shot
of the shooter (the other vehicle of a received hit, the player's vehicle of a dealt one) with the hit's shell kind,
set as the armor page sets its attacker's shell (setShellParamsFromVehicle) whenever the hits panel changes; the
armor tooltip (armor_tooltip.py) reads it and the chosen type.
"""
import logging

import BigWorld
from account_helpers.settings_core import settings_constants
from helpers import dependency
from items import parseIntCompactDescr
from items.vehicles import VehicleDescr
from skeletons.account_helpers.settings_core import ISettingsCore
from skeletons.gui.shared.utils import IHangarSpace

from gui.mods.sagtary_armor_hits.data.client_names import clientText
from gui.mods.sagtary_armor_hits.views.hits.hits_panel import DEALT
from gui.mods.sagtary_armor_hits.views.models.overlay_panel_model import OverlayItemModel, OverlayScaleModel

_logger = logging.getLogger('sagtary.armor_hits')

# The ids of the client's armor page modes (armor_model.Modes).
NO_OVERLAY = 'no_armor'
NOMINAL = 'nominal'
PENETRATION = 'penetration'
# The overlay types of the client's armor page menu, by their text keys.
_OVERLAYS = (
    (NO_OVERLAY, '#armor_inspector:menu/no_armor'),
    (NOMINAL, '#armor_inspector:menu/nominal'),
    (PENETRATION, '#armor_inspector:menu/penetration'),
)
_TITLE_KEY = '#armor_inspector:menu/header'
_MAIN_KEY = '#armor_inspector:armorValues/title/main'
_SPACED_KEY = '#armor_inspector:armorValues/title/spaced'
_PENETRATION_KEY = '#armor_inspector:armorValues/title/penetration'
_MM_KEY = '#armor_inspector:armorValues/title/values'
_PERCENT_KEY = '#armor_inspector:armorValues/title/percent'
# Seconds between taking an overlay off and putting another on: the component system takes the removal in its next
# update, and the vehicle's game object still has the component until then.
_SHOW_DELAY = 0.1
# The scale gradients of the armor page; '_cb' for color blindness.
_IMAGE = 'img://gui/maps/icons/armor_inspector/%s%s.png'


def _maxArmor(vehicleEntity):
    # (main, spaced) thickest armor of the vehicle in mm, as the armor page finds it, or None.
    if vehicleEntity is None:
        return None
    try:
        from gui.impl.lobby.vehicle_hub.sub_presenters.armor.utils import getMaxArmor
        return getMaxArmor(vehicleEntity)
    except Exception:
        _logger.debug('overlay panel: no armor of the hangar vehicle', exc_info=True)
        return None


def _vehicleDescriptor(vehicleId, descr):
    # The vehicle descriptor with its modules (compact descriptor, hex) or the default ones, None when not known.
    try:
        if descr:
            return VehicleDescr(compactDescr=descr.decode('hex'))
        _, nationID, typeID = parseIntCompactDescr(vehicleId)
        return VehicleDescr(typeID=(nationID, typeID))
    except Exception:
        _logger.debug('overlay panel: no descriptor of vehicle %s', vehicleId, exc_info=True)
        return None


def _hitShot(battle, side, hit):
    # The gun's shot the hit was fired with: of the shooter's gun with the hit's shell kind (and premium or not), else
    # of another gun of the shooter's type; None when not known.
    if battle is None or hit is None or not hit.shellType:
        return None
    if side == DEALT:
        descriptor = _vehicleDescriptor(battle.vehicleId, battle.vehicleDescr)
    else:
        descriptor = _vehicleDescriptor(hit.vehicleId, hit.vehicleDescr)
    if descriptor is None:
        return None
    guns = [descriptor.gun]
    for turrets in descriptor.type.turrets:
        for turret in reversed(turrets):
            guns.extend(reversed(turret.guns))
    shots = [shot for gun in guns for shot in gun.shots if shot.shell.kind == hit.shellType]
    for shot in shots:
        if bool(shot.shell.isGold) == bool(hit.isGoldShell):
            return shot
    return shots[0] if shots else None


class OverlayPanelPresenter(object):
    __hangarSpace = dependency.descriptor(IHangarSpace)
    __settingsCore = dependency.descriptor(ISettingsCore)

    def __init__(self, model, hitsPanel):
        self._model = model
        self._hitsPanel = hitsPanel
        self._selected = NOMINAL
        # (main, spaced) of the hangar vehicle, None without one.
        self._maxArmor = None
        # The game object the armor inspector component was put on.
        self._gameObject = None
        # The chosen hit's shell (penetration_utils.ShellParams), None when not known.
        self.shellParams = None
        # The overlay put on after the removed one has gone.
        self._callbackID = None

    @property
    def selected(self):
        # The chosen overlay type, an id of the client's armor page modes.
        return self._selected

    def init(self):
        with self._model.transaction() as model:
            model.setTitle(clientText(_TITLE_KEY) or '')
            items = model.getItems()
            items.clear()
            for overlayId, key in _OVERLAYS:
                item = OverlayItemModel()
                item.setId(overlayId)
                item.setLabel(clientText(key) or overlayId)
                items.addViewModel(item)
            items.invalidate()
        self._model.onSelect += self._onSelect
        self.__hangarSpace.onVehicleChangeStarted += self._onVehicleChangeStarted
        self.__hangarSpace.onVehicleChanged += self._onVehicleChanged
        self._hitsPanel.onChanged += self._setShell
        self._setShell()
        self._onVehicleChanged()

    def fini(self):
        self._hitsPanel.onChanged -= self._setShell
        self.__hangarSpace.onVehicleChanged -= self._onVehicleChanged
        self.__hangarSpace.onVehicleChangeStarted -= self._onVehicleChangeStarted
        self._model.onSelect -= self._onSelect
        self._removeOverlay()
        self._model = None
        self._hitsPanel = None

    def _onSelect(self, args=None):
        overlayId = (args or {}).get('id')
        if overlayId in [item for item, _ in _OVERLAYS] and overlayId != self._selected:
            self._selected = overlayId
            self._update()
            self._removeOverlay()
            self._callbackID = BigWorld.callback(_SHOW_DELAY, self._onShowDelay)

    def _onShowDelay(self):
        self._callbackID = None
        self._showOverlay()

    def _onVehicleChangeStarted(self, *args):
        self._removeOverlay()

    def _onVehicleChanged(self, *args):
        entity = self._vehicleEntity()
        self._maxArmor = _maxArmor(entity)
        self._update()
        if self._gameObject is None:
            self._removeOverlay()
            self._showOverlay()
        else:
            self._removeOverlay()
            self._callbackID = BigWorld.callback(_SHOW_DELAY, self._onShowDelay)

    def _vehicleEntity(self):
        return self.__hangarSpace.getVehicleEntity() if self.__hangarSpace.isModelLoaded else None

    def _showOverlay(self):
        # Puts the client's armor overlay of the chosen type on the loaded hangar vehicle.
        entity = self._vehicleEntity()
        appearance = getattr(entity, 'appearance', None) if entity is not None else None
        gameObject = getattr(appearance, 'gameObject', None) if appearance is not None else None
        if self._selected == NO_OVERLAY or gameObject is None:
            return
        try:
            from cgf_components.armor_inspector_component import ArmorInspectorComponent
            if not gameObject.hasComponent(ArmorInspectorComponent):
                component = ArmorInspectorComponent()
                component.showProbability = self._selected == PENETRATION
                gameObject.assignComponent(component)
            self._gameObject = gameObject
            _logger.info('overlay panel: %s overlay on vehicle %s', self._selected, entity.typeDescriptor.name)
        except Exception:
            _logger.exception('overlay panel: cannot show the overlay')

    def _removeOverlay(self):
        if self._callbackID is not None:
            BigWorld.cancelCallback(self._callbackID)
            self._callbackID = None
        gameObject, self._gameObject = self._gameObject, None
        if gameObject is None:
            return
        try:
            from cgf_components.armor_inspector_component import ArmorInspectorComponent
            if gameObject.findWrite(ArmorInspectorComponent) is not None:
                gameObject.removeComponent(ArmorInspectorComponent)
        except Exception:
            # The hangar has already destroyed the vehicle's game object, and the overlay with it.
            _logger.debug('overlay panel: cannot remove the overlay', exc_info=True)

    def _setShell(self):
        # The penetration chance overlay and the armor tooltip count the chance of the chosen hit's shell.
        battle, side, hit = self._hitsPanel.selection
        shot = _hitShot(battle, side, hit)
        self.shellParams = None
        if shot is None:
            return
        try:
            from gui.impl.lobby.vehicle_hub.sub_presenters.armor.penetration_utils import setShellParamsFromVehicle
            self.shellParams = setShellParamsFromVehicle(shot, self.__hangarSpace.spaceID)
            _logger.info('overlay panel: penetration chance of shell %s', shot.shell.name)
        except Exception:
            _logger.exception('overlay panel: cannot set the shell')

    def _scales(self):
        # [(title key, units key, image name, min, max)] of the chosen overlay.
        main, spaced = self._maxArmor or ('', '')
        if self._selected == NOMINAL:
            return [(_MAIN_KEY, _MM_KEY, 'main_armor', '0', str(main)),
                    (_SPACED_KEY, _MM_KEY, 'spaced_armor', '0', str(spaced))]
        if self._selected == PENETRATION:
            return [(_PENETRATION_KEY, _PERCENT_KEY, 'penetration_chance', '0', '100')]
        return []

    def _update(self):
        colorBlind = '_cb' if self.__settingsCore.getSetting(settings_constants.GRAPHICS.COLOR_BLIND) else ''
        with self._model.transaction() as model:
            model.setSelectedId(self._selected)
            scales = model.getScales()
            scales.clear()
            for titleKey, unitsKey, image, minValue, maxValue in self._scales():
                scale = OverlayScaleModel()
                scale.setTitle(clientText(titleKey) or '')
                scale.setUnits(clientText(unitsKey) or '')
                scale.setImage(_IMAGE % (image, colorBlind))
                scale.setMinValue(minValue)
                scale.setMaxValue(maxValue)
                scales.addViewModel(scale)
            scales.invalidate()
