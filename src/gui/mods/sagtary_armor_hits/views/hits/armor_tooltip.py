# -*- coding: utf-8 -*-
"""Armor tooltip of the hits screen: the armor under the mouse on the hangar vehicle, like on the client's armor page.

ArmorTooltipPresenter does what the armor page presenter does for its tooltip (ArmorSubPresenter): while the mouse is
over the 3D scene (HangarSpace.isCursorOver3DScene, which the page tells the client) it looks every _TICK seconds and
finds the armor under the mouse (getCollisionsAtCursor) and shows the client's tooltip window (ArmorTooltipWindow:
the armor layers, their nominal and resulting armor, the angle, the penetration chance of the shell) at the mouse,
with the client's armor cursor. The tooltip goes when the mouse leaves the vehicle or the scene. The armor page shows
the tooltip only over the vehicle the client has focused (HangarSpace.onMouseEnter), which needs the hangar's object
selection; this one shows it wherever the mouse ray hits the vehicle. The armor page updates its tooltip on the
mouse events of the game (gui.g_mouseEventHandlers), but the page's layer over the scene takes the mouse moves, so the
game does not get them all. The shell and the overlay type are the overlay
panel's (overlay_panel.py): the chosen hit's shell.
"""
import logging

import BigWorld
import GUI
from frameworks.wulf import ViewStatus
from helpers import dependency
from skeletons.account_helpers.settings_core import ISettingsCore
from skeletons.gui.shared.utils import IHangarSpace

_logger = logging.getLogger('sagtary.armor_hits')

# Seconds between the looks under the mouse.
_TICK = 0.03


class ArmorTooltipPresenter(object):
    __hangarSpace = dependency.descriptor(IHangarSpace)
    __settingsCore = dependency.descriptor(ISettingsCore)

    def __init__(self, overlayPanel):
        self._overlayPanel = overlayPanel
        self._tooltip = None
        self._callbackID = None

    def init(self):
        self.__hangarSpace.onNotifyCursorOver3dScene += self._onCursorOverScene
        self.__hangarSpace.onVehicleChangeStarted += self._onVehicleChangeStarted
        self._onCursorOverScene(self.__hangarSpace.isCursorOver3DScene)

    def fini(self):
        self.__hangarSpace.onVehicleChangeStarted -= self._onVehicleChangeStarted
        self.__hangarSpace.onNotifyCursorOver3dScene -= self._onCursorOverScene
        self._stop()
        self._destroy()
        self._overlayPanel = None

    def _onCursorOverScene(self, isOver):
        if isOver and self._callbackID is None:
            self._callbackID = BigWorld.callback(0.0, self._onTick)
        elif not isOver:
            self._stop()
            self._destroy()

    def _stop(self):
        if self._callbackID is not None:
            BigWorld.cancelCallback(self._callbackID)
            self._callbackID = None

    def _onVehicleChangeStarted(self, *args):
        self._destroy()

    def _onTick(self):
        self._callbackID = BigWorld.callback(_TICK, self._onTick)
        try:
            self._update()
        except Exception:
            _logger.exception('armor tooltip: cannot update')
            self._stop()
            self._destroy()

    def _update(self):
        cursor = GUI.mcursor()
        entity = self.__hangarSpace.getVehicleEntity() if self.__hangarSpace.isModelLoaded else None
        collisions = None
        if entity is not None and cursor.inWindow and cursor.inFocus and self.__hangarSpace.isCursorOver3DScene:
            from gui.impl.lobby.vehicle_hub.sub_presenters.armor.utils import getCollisionsAtCursor
            collisions = getCollisionsAtCursor(entity)
        if not collisions:
            self._destroy()
            return
        if self._tooltip is None:
            from gui.impl.lobby.vehicle_hub.sub_presenters.armor.armor_tooltip import ArmorTooltipWindow
            self._tooltip = ArmorTooltipWindow(entity)
            self._tooltip.onStatusChanged += self._onStatusChanged
            self._move()
            self._tooltip.update(self._overlayPanel.selected, self._overlayPanel.shellParams, collisions)
            self._tooltip.load()
            GUI.switchArmorInspectorCursor(True)
            return
        self._move()
        self._tooltip.update(self._overlayPanel.selected, self._overlayPanel.shellParams, collisions)

    def _move(self):
        # The mouse in pixels of the interface, as the armor page places its tooltip.
        from gui.impl.lobby.vehicle_hub.sub_presenters.armor.utils import getCursorPositionInPixels
        x, y = getCursorPositionInPixels()
        scale = self.__settingsCore.interfaceScale.get()
        if scale != 1:
            x, y = int(x // scale), int(y // scale)
        self._tooltip.move(x, y)

    def _onStatusChanged(self, status):
        if status == ViewStatus.DESTROYED:
            self._destroy()

    def _destroy(self):
        tooltip, self._tooltip = self._tooltip, None
        if tooltip is None:
            return
        tooltip.onStatusChanged -= self._onStatusChanged
        tooltip.destroy()
        GUI.switchArmorInspectorCursor(False)
