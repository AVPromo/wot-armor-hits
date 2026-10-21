# -*- coding: utf-8 -*-
"""Hit lines of the hits screen: the shells' ways of the hits, drawn in the 3D scene over the hangar vehicle, and
the shooter view.

HitLinesPresenter draws on the vehicle the hangar shows (hangar_vehicle.py) the way of the hit the hits panel has
chosen and, when the scene panel asks for all lines, the ways of the other hits the panel shows. The chosen hit's way
A way is in the color of the hit's result (_RESULT_COLOURS: red for damage, orange for a critical hit without damage,
grey for a blocked hit), on both sides: the chosen hit's dashed in that color and black, from the color, the others
solid. The pieces are tubes drawn with the client's debug drawer (scene_lines.py): over the client's armor overlay,
hidden behind the vehicle.

With the shooter view on, the hangar camera looks along the chosen hit's shell at its first point
(HangarCameraSystem.moveCamera); turned off, the camera goes back to its place (resetCameraTarget). The scene panel's
reset puts the camera back the same way: behind the shell with the shooter view on, else to its place.

When it draws: a hit is chosen and the hangar already shows its vehicle, loaded: at once; otherwise the hangar
vehicle presenter has asked for the vehicle, and the lines are drawn when the hangar tells it has loaded it
(HangarSpace.onVehicleChanged; the parts of the vehicle are in their places then). The lines are removed when the
hangar starts to change the vehicle (onVehicleChangeStarted) and drawn again when the hits or the choices change.

The way of a shell, from its points (Hit.points): a piece of _LEAD metres before the first point, along the shell's
direction there; a piece to the next point after a ricochet or spaced armor, where the shell goes on (it hits the
vehicle again, or its main armor behind the spaced one); after a ricochet that is the last point, a piece of
_RICOCHET metres in the mirrored direction (the client does not tell where the shell went). The way after a
penetration is not drawn. A high explosive shell bursts at its first point: its other points are what the burst hit,
not its way, so only the way to the first point is drawn. A splash (Hit.splashCenter) has no points: a cross of
_BURST metres where the shell burst and a post from there down (or up) to the level of the vehicle's tracks, the
chassis space's ground: the shell burst on a slope, in a hole or on a rock or a wall, while the hangar's floor is
flat. The explosion radius is not drawn: about 10 m for a big gun, it covers the hangar.

A point is the middle of the shell's way through the part the server sends, and the shell's direction is along that
way, like the Battle Hits mod places its hits: data only, so a point does not wait for the vehicle's collision model.
At the first point the direction is the shell's exact one from its tracer when the hit has it (Hit.shotDirection):
the server packs the way to 1/255 of the part on each axis, a degree or so off along a short way.
The model is needed only for the armor's normal at a last ricochet; it comes a few frames after the vehicle, so
without it the lines are drawn again after _NORMAL_RETRY seconds, up to _NORMAL_TRIES times, and then without the
ricochet's way out.
"""
import logging

import BigWorld
import CGF
from Event import Event
import Math
from cgf_components.hangar_camera_manager import HangarCameraSystem
from constants import SHELL_TYPES, VEHICLE_HIT_EFFECT
from helpers import dependency
from skeletons.gui.shared.utils import IHangarSpace
from vehicle_systems.tankStructure import TankPartIndexes, TankPartNames

from gui.mods.sagtary_armor_hits.data.hits import HitResult
from gui.mods.sagtary_armor_hits.views.hits.hangar_vehicle import hitsVehicle
from gui.mods.sagtary_armor_hits.views.hits.scene_lines import SceneLines
from gui.mods.sagtary_armor_hits.views.hits.scene_log import sceneState
from gui.mods.sagtary_armor_hits.trace import calls, effectsText, modulesText

_logger = logging.getLogger('sagtary.armor_hits')

# The colors (ARGB) of a way's dashes: the color of the hit's result, then black, in turn.
_DASH_BLACK = 0xFF101010
_RESULT_COLOURS = {
    HitResult.DAMAGE: 0xFFFF3020,
    HitResult.BLOCKED: 0xFF9A9A9A,
    HitResult.RICOCHET: 0xFFD880D8,
    HitResult.NO_DAMAGE: 0xFFA8E0E2,
}
# Metres: the way drawn before the first point and after a ricochet.
_LEAD = 2.5
_RICOCHET = 1.5
# Metres: the arms of a splash's burst cross.
_BURST = 0.3
_NORMAL_RETRY = 0.2
_NORMAL_TRIES = 5
# The shooter view: the camera's distance to the hit point in metres and its flight in seconds.
_SHOOTER_DISTANCE = 6.0
_CAMERA_FLIGHT = 0.5
_RICOCHETS = (VEHICLE_HIT_EFFECT.INTERMEDIATE_RICOCHET, VEHICLE_HIT_EFFECT.FINAL_RICOCHET)
# The points after which the shell goes on to the next one.
_GOES_ON = _RICOCHETS + (VEHICLE_HIT_EFFECT.ARMOR_PIERCED_NO_DAMAGE,)


def _text(vector):
    return '(%.2f, %.2f, %.2f)' % (vector.x, vector.y, vector.z)


def _unit(vector):
    vector = Math.Vector3(vector)
    vector.normalise()
    return vector


def _partNode(compoundModel, part):
    # The world matrix of the node the client puts the hit effects of the part on (the part's space), or None.
    nodeName = TankPartNames.getActualNodeNameByPartName(TankPartIndexes.getName(part))
    try:
        return Math.Matrix(compoundModel.node(nodeName))
    except Exception:
        _logger.debug('hit lines: no node %s', nodeName)
        return None


def _armorNormal(collisions, point):
    # The armor's normal at the point in the part's space from the collision model, or None when the model does not
    # have the point (not loaded yet, other modules): the collision must lie on the shell's way.
    if collisions is None:
        return None
    start, end = Math.Vector3(*point.start), Math.Vector3(*point.end)
    try:
        distance, _, normal, _ = collisions.collideLocal(point.part, start, end)
    except Exception:
        _logger.debug('hit lines: no collision of part %s', point.part, exc_info=True)
        return None
    if distance < 0.0 or distance > (end - start).length + 0.01 or not 0.5 < Math.Vector3(normal).length < 1.5:
        return None
    return _unit(normal)


def _drawn(hit):
    # The hit has something to draw: its points or where its splash burst.
    return bool(hit.points or hit.splashCenter)


def _splashWay(hit, compoundModel):
    # ([(start, end)] pieces of a splash: the burst cross and its post to the tracks' level, (burst, the direction to
    # the vehicle)).
    chassis = _partNode(compoundModel, TankPartIndexes.CHASSIS)
    if chassis is None:
        return [], None
    x, y, z = hit.splashCenter
    center = chassis.applyPoint(Math.Vector3(x, y, z))
    foot = chassis.applyPoint(Math.Vector3(x, 0.0, z))
    pieces = [(center - axis * _BURST, center + axis * _BURST) for axis in (
        _unit(chassis.applyVector(Math.Vector3(1, 0, 0))), _unit(chassis.applyVector(Math.Vector3(0, 1, 0))),
        _unit(chassis.applyVector(Math.Vector3(0, 0, 1))))]
    if abs(y) > _BURST:
        pieces.append((center, foot))
    direction = chassis.translation - center
    if direction.length < 1e-3:
        direction = chassis.applyVector(Math.Vector3(0, 0, 1))
    return pieces, (center, _unit(direction))


def _hitWay(hit, compoundModel, collisions):
    # ([(start, end)] pieces of the hit's way in the scene, (first point, shell direction) or None, whether a
    # ricochet's way out waits for the collision model).
    if not hit.points and hit.splashCenter:
        return _splashWay(hit, compoundModel) + (False,)
    points = []
    for point in hit.points:
        start, end = Math.Vector3(*point.start), Math.Vector3(*point.end)
        matrix = _partNode(compoundModel, point.part)
        if matrix is None or (end - start).length < 1e-6:
            continue
        points.append((point, matrix, matrix.applyPoint((start + end) * 0.5), _unit(matrix.applyVector(end - start))))
    if hit.shellType == SHELL_TYPES.HIGH_EXPLOSIVE:
        points = points[:1]
    if not points:
        return [], None, False
    if hit.shotDirection:
        point, matrix, position, _ = points[0]
        points[0] = (point, matrix, position, _unit(matrix.applyVector(Math.Vector3(*hit.shotDirection))))
    pieces = [(points[0][2] - points[0][3] * _LEAD, points[0][2])]
    waitsNormal = False
    for previous, current in zip(points, points[1:]):
        if previous[0].effect not in _GOES_ON:
            break
        pieces.append((previous[2], current[2]))
    else:
        point, matrix, position, direction = points[-1]
        if point.effect in _RICOCHETS:
            normal = _armorNormal(collisions, point)
            if normal is not None:
                normal = _unit(matrix.applyVector(normal))
                mirrored = _unit(direction - normal * (2 * direction.dot(normal)))
                pieces.append((position, position + mirrored * _RICOCHET))
            else:
                waitsNormal = True
    return pieces, (points[0][2], points[0][3]), waitsNormal


def _checkPoints(hit, collisions):
    # The log of where the hangar vehicle's armor is on the way of each of the hit's points: a point without armor on
    # its way is on other modules or another vehicle than the hangar's.
    for index, point in enumerate(hit.points):
        start, end = Math.Vector3(*point.start), Math.Vector3(*point.end)
        text = 'no collision model'
        if collisions is not None:
            try:
                found = collisions.collideLocal(point.part, start, end)
            except Exception:
                found = None
            if found is None or found[0] < 0.0:
                text = 'NO ARMOR on the way (other modules or another vehicle?)'
            else:
                text = 'armor at %.3f m of the %.3f m way' % (found[0], (end - start).length)
        _logger.info('check: hit lines: point %d, part %s, %s: %s', index, point.part,
                     effectsText((point.effect,)), text)


def _colours(hit):
    # The colors of the chosen hit's dashes in turn: the result's color first, then black.
    return _RESULT_COLOURS.get(hit.result, _RESULT_COLOURS[HitResult.BLOCKED]), _DASH_BLACK


class HitLinesPresenter(object):
    __hangarSpace = dependency.descriptor(IHangarSpace)

    def __init__(self, hitsPanel, scenePanel):
        self._hitsPanel = hitsPanel
        self._scenePanel = scenePanel
        # (vehicle, chosen hit, other hits) to draw: the hangar vehicle the hits are on (hangar_vehicle.hitsVehicle),
        # the chosen hit or None, the other shown hits when all lines are asked for.
        self._target = None
        self._lines = SceneLines()
        # The next drawing while the collision model has not come, and how many were done for that.
        self._callbackID = None
        self._normalTries = 0
        # The camera was moved for the shooter view.
        self._cameraMoved = False
        # (first point, shell direction) of the chosen hit as last drawn, None without it; told by onDrawn.
        self.chosenShot = None
        self.onDrawn = Event()

    def init(self):
        self.__hangarSpace.onVehicleChangeStarted += self._onVehicleChangeStarted
        self.__hangarSpace.onVehicleChanged += self._onVehicleChanged
        self._hitsPanel.onChanged += self._update
        self._scenePanel.onChanged += self._onScenePanelChanged
        self._scenePanel.onResetCamera += self._onResetCamera
        self._update()

    def fini(self):
        self._scenePanel.onResetCamera -= self._onResetCamera
        self._scenePanel.onChanged -= self._onScenePanelChanged
        self._hitsPanel.onChanged -= self._update
        self.__hangarSpace.onVehicleChanged -= self._onVehicleChanged
        self.__hangarSpace.onVehicleChangeStarted -= self._onVehicleChangeStarted
        self._clear()
        self.onDrawn.clear()
        self._hitsPanel = None
        self._scenePanel = None

    def _update(self):
        # The hits or the choices changed: drawn at once when the hangar shows their vehicle, else when it has loaded.
        battle, side, hit = self._hitsPanel.selection
        vehicle = hitsVehicle(battle, side, hit)
        others = ()
        if self._scenePanel.showsAllLines:
            selected = self._hitsPanel.selectedNumber
            others = tuple(other for number, other in self._hitsPanel.shownHits if number != selected and _drawn(other))
        chosen = hit if hit is not None and _drawn(hit) else None
        target = (vehicle, chosen, others) if isinstance(vehicle, tuple) and (chosen or others) else None
        calls('hit lines: update')
        _logger.info('scene: hit lines: selection battle %s, side %s, hit at %s with %d points, %d other hits, '
                     'vehicle %s; %s', battle.battleId if battle is not None else None, side,
                     hit.time if hit is not None else None, len(hit.points) if hit is not None else 0, len(others),
                     vehicle[0] if isinstance(vehicle, tuple) else vehicle,
                     'same target' if target == self._target else 'new target')
        if target == self._target:
            return
        self._target = target
        self._clear()
        if target is not None:
            self._draw('hits chosen')

    def _onScenePanelChanged(self):
        calls('hit lines: scene panel changed')
        if not self._scenePanel.shooterView and self._cameraMoved:
            self._resetCamera()
        self._target = None
        self._update()

    def _onResetCamera(self):
        calls('hit lines: reset camera', 'shooter view %s, line %s' % (self._scenePanel.shooterView,
                                                                     self.chosenShot is not None))
        if self._scenePanel.shooterView and self.chosenShot is not None:
            self._moveCamera(*self.chosenShot)
        else:
            self._resetCamera()

    def _onVehicleChangeStarted(self, *args):
        calls('hit lines: vehicle change started')
        self._clear()

    def _onVehicleChanged(self, *args):
        calls('hit lines: vehicle changed', 'target %s' % (self._target is not None))
        if self._target is not None:
            self._clear()
            self._draw('vehicle loaded')

    def _hangarModel(self):
        # (compound model, collisions) of the hangar vehicle when it is the vehicle of the hits and has loaded.
        if not self.__hangarSpace.isModelLoaded:
            return None
        entity = self.__hangarSpace.getVehicleEntity()
        descriptor = getattr(entity, 'typeDescriptor', None) if entity is not None else None
        if descriptor is None or descriptor.type.compactDescr != self._target[0][0]:
            return None
        appearance = getattr(entity, 'appearance', None)
        compoundModel = getattr(appearance, 'compoundModel', None) if appearance is not None else None
        if compoundModel is None:
            return None
        return compoundModel, getattr(appearance, 'collisions', None)

    def _draw(self, reason):
        calls('hit lines: draw', reason)
        hangarModel = self._hangarModel()
        if hangarModel is None:
            _logger.info('scene: hit lines: %s, not the vehicle of the hits yet: %s', reason, sceneState())
            return
        try:
            self._drawOn(reason, *hangarModel)
        except Exception:
            _logger.exception('hit lines: cannot draw')

    def _drawOn(self, reason, compoundModel, collisions):
        _, chosen, others = self._target
        waitsNormal = False
        for hit in others:
            pieces, _, waits = _hitWay(hit, compoundModel, collisions)
            waitsNormal = waitsNormal or waits
            for start, end in pieces:
                self._lines.add(start, end, _colours(hit)[:1])
        first = None
        if chosen is not None:
            pieces, first, waits = _hitWay(chosen, compoundModel, collisions)
            waitsNormal = waitsNormal or waits
            for start, end in pieces:
                self._lines.add(start, end, _colours(chosen))
            if chosen.splashCenter and not chosen.points:
                _logger.info('check: hit lines: splash at %s of the chassis', chosen.splashCenter)
        if waitsNormal and self._normalTries < _NORMAL_TRIES:
            self._normalTries += 1
            self._callbackID = BigWorld.callback(_NORMAL_RETRY, self._onNormalRetry)
        if first is not None and self._scenePanel.shooterView:
            self._moveCamera(*first)
        if chosen is not None:
            entity = self.__hangarSpace.getVehicleEntity()
            _logger.info('check: hit lines: drawn on %s', modulesText(getattr(entity, 'typeDescriptor', None)))
            _checkPoints(chosen, collisions)
        self.chosenShot = first
        calls('hit lines: onDrawn', 'drawn, %d listeners' % len(self.onDrawn))
        self.onDrawn()
        _logger.info('scene: hit lines: %s: %d dashes, %d other hits, chosen hit at %s, direction %s', reason,
                     len(self._lines), len(others), _text(first[0]) if first else None,
                     _text(first[1]) if first else None)

    def _onNormalRetry(self):
        self._callbackID = None
        _logger.info('scene: hit lines: again for the ricochet normal (%d)', self._normalTries)
        self._lines.clear()
        self._draw('ricochet normal')

    def _moveCamera(self, position, direction):
        # The shooter view: the camera behind the shell, looking along it at its first point.
        camera = CGF.getSystem(self.__hangarSpace.spaceID, HangarCameraSystem)
        if camera is None:
            return
        camera.moveCamera(targetPos=position, yaw=direction.yaw, pitch=-direction.pitch, distance=_SHOOTER_DISTANCE,
                          duration=_CAMERA_FLIGHT)
        self._cameraMoved = True

    def _resetCamera(self):
        self._cameraMoved = False
        camera = CGF.getSystem(self.__hangarSpace.spaceID, HangarCameraSystem)
        if camera is not None:
            camera.resetCameraTarget(duration=_CAMERA_FLIGHT)

    def _clear(self):
        # Removes the lines and forgets the drawing that waits for the collision model.
        if self._callbackID is not None:
            BigWorld.cancelCallback(self._callbackID)
            self._callbackID = None
        self._normalTries = 0
        self._lines.clear()
        calls('hit lines: clear', 'chosen line %s' % (self.chosenShot is not None))
        if self.chosenShot is not None:
            self.chosenShot = None
            calls('hit lines: onDrawn', 'cleared, %d listeners' % len(self.onDrawn))
            self.onDrawn()
