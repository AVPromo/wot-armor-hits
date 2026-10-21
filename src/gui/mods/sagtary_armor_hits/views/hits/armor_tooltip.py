# -*- coding: utf-8 -*-
"""Armor tooltip of the hits screen: the armor under the mouse on the hangar vehicle, like on the client's armor page.

ArmorTooltipPresenter does what the armor page presenter does for its tooltip (ArmorSubPresenter): while the screen
is open it looks every _TICK seconds whether the mouse is over the 3D scene (HangarSpace.isCursorOver3DScene, which
the page tells the client), finds the armor under the mouse (getCollisionsAtCursor) and shows the client's tooltip
window (ArmorTooltipWindow: the armor layers, their nominal and resulting armor, the angle, the penetration chance of
the shell) at the mouse, with the client's armor cursor. The tooltip goes when the mouse leaves the vehicle, or the
scene for _AWAY seconds: the page tells the mouse left the scene for a frame now and then. The window is made once
as soon as the vehicle has loaded, off the screen, so that its page has loaded before the mouse comes (the first
load of the client's tooltip page takes a while); then it is moved to the mouse, hidden when the tooltip goes and
shown again when it comes back. The window keeps the hangar's vehicle entity, which stays the same for another
vehicle: the window stays too (a new window shows late the first time), made again only for another entity. Once its
page has loaded it is filled off the screen with the armor along the camera's ray to the vehicle, so that its first
showing at the mouse has its layout made. The armor page
shows the tooltip only over the vehicle the client has focused (HangarSpace.onMouseEnter), which needs the hangar's
object selection; this one shows it wherever the mouse ray hits the vehicle. The armor page updates its tooltip on
the mouse events of the game (gui.g_mouseEventHandlers), but the page's layer over the scene takes the mouse moves, so
the game does not get them all. The shell and the overlay type are the overlay panel's (overlay_panel.py): the chosen
hit's shell.
"""
import logging

import BigWorld
import GUI
import Math
from frameworks.wulf import WindowStatus
from helpers import dependency
from skeletons.account_helpers.settings_core import ISettingsCore
from skeletons.gui.shared.utils import IHangarSpace

from gui.mods.sagtary_armor_hits.trace import calls

_logger = logging.getLogger('sagtary.armor_hits')

# Seconds between the looks under the mouse; seconds the mouse is away from the scene before the tooltip goes.
_TICK = 0.03
_AWAY = 0.15
# Pixels of the interface where the window waits for the mouse: off the screen.
_OFF_SCREEN = -4000


class ArmorTooltipPresenter(object):
    __hangarSpace = dependency.descriptor(IHangarSpace)
    __settingsCore = dependency.descriptor(ISettingsCore)

    def __init__(self, overlayPanel):
        self._overlayPanel = overlayPanel
        self._tooltip = None
        self._callbackID = None
        # BigWorld.time() the mouse left the scene at, None while over it.
        self._awaySince = None
        # The tooltip window is shown (not hidden); BigWorld.time() it was made at, for the log of its loading; the
        # vehicle entity it was made for.
        self._shown = False
        self._madeAt = 0.0
        self._entity = None

    def init(self):
        self.__hangarSpace.onNotifyCursorOver3dScene += self._onCursorOverScene
        self.__hangarSpace.onVehicleChangeStarted += self._onVehicleChangeStarted
        self._callbackID = BigWorld.callback(0.0, self._onTick)

    def fini(self):
        self.__hangarSpace.onVehicleChangeStarted -= self._onVehicleChangeStarted
        self.__hangarSpace.onNotifyCursorOver3dScene -= self._onCursorOverScene
        self._stop()
        self._destroy()
        self._overlayPanel = None

    @staticmethod
    def _onCursorOverScene(isOver):
        calls('armor tooltip: cursor over scene', '%s' % isOver)

    def _stop(self):
        if self._callbackID is not None:
            BigWorld.cancelCallback(self._callbackID)
            self._callbackID = None

    def _onVehicleChangeStarted(self, *args):
        self._hide()

    def _onTick(self):
        self._callbackID = BigWorld.callback(_TICK, self._onTick)
        calls('armor tooltip: tick', quiet=True)
        try:
            self._update()
        except Exception:
            _logger.exception('armor tooltip: cannot update')
            self._stop()
            self._destroy()

    def _update(self):
        entity = self.__hangarSpace.getVehicleEntity() if self.__hangarSpace.isModelLoaded else None
        if entity is not None and entity is not self._entity:
            self._destroy()
            self._make(entity)
        cursor = GUI.mcursor()
        if not (cursor.inWindow and cursor.inFocus and self.__hangarSpace.isCursorOver3DScene):
            now = BigWorld.time()
            if self._awaySince is None:
                self._awaySince = now
            if now - self._awaySince >= _AWAY:
                self._hide()
            return
        self._awaySince = None
        collisions = None
        if entity is not None and self._tooltip is not None:
            from gui.impl.lobby.vehicle_hub.sub_presenters.armor.utils import getCollisionsAtCursor
            collisions = getCollisionsAtCursor(entity)
        if not collisions:
            self._hide()
            return
        self._move()
        self._tooltip.update(self._overlayPanel.selected, self._overlayPanel.shellParams, collisions)
        if not self._shown:
            calls('armor tooltip: show')
            self._tooltip.show(focus=False)
            self._shown = True
            GUI.switchArmorInspectorCursor(True)

    def _make(self, entity):
        # The tooltip window of the vehicle, loaded off the screen; shown at the mouse when there is armor under it.
        from gui.impl.lobby.vehicle_hub.sub_presenters.armor.armor_tooltip import ArmorTooltipWindow
        calls('armor tooltip: create')
        self._tooltip = ArmorTooltipWindow(entity)
        self._entity = entity
        self._tooltip.onStatusChanged += self._onStatusChanged
        self._tooltip.content.onStatusChanged += self._onViewStatusChanged
        self._madeAt = BigWorld.time()
        self._tooltip.move(_OFF_SCREEN, _OFF_SCREEN)
        self._tooltip.load()
        self._shown = False

    def _move(self):
        # The mouse in pixels of the interface, as the armor page places its tooltip.
        from gui.impl.lobby.vehicle_hub.sub_presenters.armor.utils import getCursorPositionInPixels
        x, y = getCursorPositionInPixels()
        scale = self.__settingsCore.interfaceScale.get()
        if scale != 1:
            x, y = int(x // scale), int(y // scale)
        self._tooltip.move(x, y)

    def _onStatusChanged(self, status):
        _logger.info('armor tooltip: window status %s at %.0f ms', status, (BigWorld.time() - self._madeAt) * 1000)
        if status == WindowStatus.LOADED:
            self._warmUp()
        elif status == WindowStatus.DESTROYED:
            self._destroy()

    def _warmUp(self):
        # The window off the screen filled with the armor along the camera's ray to the vehicle's middle.
        entity = self._entity
        collisions = getattr(getattr(entity, 'appearance', None), 'collisions', None)
        if self._tooltip is None or collisions is None or self._shown:
            return
        from helpers.collisions import SegmentCollisionResultExt
        from shared_utils.vehicle_utils import getMatinfo
        start = Math.Matrix(BigWorld.camera().invViewMatrix).translation
        end = entity.position + Math.Vector3(0.0, 1.0, 0.0)
        found = collisions.collideAllWorld(start, start + (end - start) * 2.0) or ()
        isWheeled = entity.typeDescriptor.type.isWheeledVehicle
        segments = [SegmentCollisionResultExt(distance, angleCos, getMatinfo(entity, part, kind, isWheeled), part)
                    for distance, angleCos, kind, part in found]
        self._tooltip.update(self._overlayPanel.selected, self._overlayPanel.shellParams, segments)
        _logger.info('armor tooltip: filled off the screen with %d layers', len(segments))

    def _onViewStatusChanged(self, status):
        _logger.info('armor tooltip: page status %s at %.0f ms', status, (BigWorld.time() - self._madeAt) * 1000)

    def _hide(self):
        if self._tooltip is None or not self._shown:
            return
        calls('armor tooltip: hide')
        self._tooltip.hide()
        self._shown = False
        GUI.switchArmorInspectorCursor(False)

    def _destroy(self):
        tooltip, self._tooltip = self._tooltip, None
        if tooltip is None:
            return
        calls('armor tooltip: destroy')
        tooltip.onStatusChanged -= self._onStatusChanged
        tooltip.content.onStatusChanged -= self._onViewStatusChanged
        tooltip.destroy()
        self._entity = None
        if self._shown:
            GUI.switchArmorInspectorCursor(False)
        self._shown = False
