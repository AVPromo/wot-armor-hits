# -*- coding: utf-8 -*-
"""Hit lines of the hits screen: the shell's way of the chosen hit, drawn in the 3D scene over the hangar vehicle.

HitLinesPresenter draws the way of the hit the hits panel has chosen on the vehicle the hangar shows for it
(hangar_vehicle.py). Each piece of the way is dashed in the colors of _DASH_LINES, _DASH metres each, from its
start; a dash is a model in the hangar space: the mod's line of its color, a tube 1 m long and wide with the client's
glow shader (like the lines of the Battle Hits mod; tools/make_line_model.py makes them), stretched along the dash
and _THICKNESS thin by its motor's matrix. The vehicle hides what is behind it.

When it draws: a hit is chosen and the hangar already shows its vehicle, loaded: at once; otherwise the hangar
vehicle presenter has asked for the vehicle, and the lines are drawn when the hangar tells it has loaded it
(HangarSpace.onVehicleChanged; the parts of the vehicle are in their places then). The lines are removed when the
hangar starts to change the vehicle (onVehicleChangeStarted) and when another hit is chosen.

The way of a shell, from its points (Hit.points): a piece of _LEAD metres before the first point, along the shell's
direction there; a piece to the next point after a ricochet or spaced armor, where the shell goes on (it hits the
vehicle again, or its main armor behind the spaced one); after a ricochet that is the last point, a piece of
_RICOCHET metres in the mirrored direction (the client does not tell where the shell went). The way after a
penetration is not drawn. A high explosive shell bursts at its first point: its other points are what the burst hit,
not its way, so only the way to the first point is drawn.

A point is the middle of the shell's way through the part the server sends, and the shell's direction is along that
way, like the Battle Hits mod places its hits: data only, so a point does not wait for the vehicle's collision model.
The model is needed only for the armor's normal at a last ricochet; it comes a few frames after the vehicle, so
without it the lines are drawn again after _NORMAL_RETRY seconds, up to _NORMAL_TRIES times, and then without the
ricochet's way out.
"""
import logging
import math

import BigWorld
import Math
from constants import SHELL_TYPES, VEHICLE_HIT_EFFECT
from helpers import dependency
from skeletons.gui.shared.utils import IHangarSpace
from vehicle_systems.tankStructure import TankPartIndexes, TankPartNames

from gui.mods.sagtary_armor_hits.views.hits.hangar_vehicle import hitsVehicle
from gui.mods.sagtary_armor_hits.views.hits.scene_log import sceneState

_logger = logging.getLogger('sagtary.armor_hits')

# Tubes 1 m long along their z axis from their origin, 1 m wide around the axis: the colors of the dashes in turn.
_DASH_LINES = ('content/sagtary_armor_hits/line_white.model', 'content/sagtary_armor_hits/line_red.model')
_DASH = 0.1
# Metres: the line's thickness, the way drawn before the first point and after a ricochet.
_THICKNESS = 0.018
_LEAD = 2.5
_RICOCHET = 1.5
_NORMAL_RETRY = 0.2
_NORMAL_TRIES = 5
_RICOCHETS = (VEHICLE_HIT_EFFECT.INTERMEDIATE_RICOCHET, VEHICLE_HIT_EFFECT.FINAL_RICOCHET)
# The points after which the shell goes on to the next one.
_GOES_ON = _RICOCHETS + (VEHICLE_HIT_EFFECT.ARMOR_PIERCED_NO_DAMAGE,)


def _text(vector):
    return '(%.2f, %.2f, %.2f)' % (vector.x, vector.y, vector.z)


def _unit(vector):
    vector = Math.Vector3(vector)
    vector.normalise()
    return vector


def _cross(a, b):
    return Math.Vector3(a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x)


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


def _segmentMatrix(start, end, thickness):
    # Maps the line onto the segment: its z axis along the segment, x and y across it, thickness wide.
    way = end - start
    forward = way * (1.0 / way.length)
    up = Math.Vector3(0, 1, 0) if abs(forward.y) < 0.99 else Math.Vector3(1, 0, 0)
    side = _unit(_cross(up, forward))
    other = _cross(forward, side)
    matrix = Math.Matrix()
    matrix.setIdentity()
    for row, vector in enumerate((side * thickness, other * thickness, way, start)):
        for column, value in enumerate((vector.x, vector.y, vector.z)):
            matrix.setElement(row, column, value)
    return matrix


class HitLinesPresenter(object):
    __hangarSpace = dependency.descriptor(IHangarSpace)

    def __init__(self, hitsPanel):
        self._hitsPanel = hitsPanel
        # (vehicle, hit) to draw: the hangar vehicle the hit is on (hangar_vehicle.hitsVehicle) and the hit.
        self._target = None
        self._models = []
        # The next drawing while the collision model has not come, and how many were done for that.
        self._callbackID = None
        self._normalTries = 0

    def init(self):
        self.__hangarSpace.onVehicleChangeStarted += self._onVehicleChangeStarted
        self.__hangarSpace.onVehicleChanged += self._onVehicleChanged
        self._hitsPanel.onChanged += self._update
        self._update()

    def fini(self):
        self._hitsPanel.onChanged -= self._update
        self.__hangarSpace.onVehicleChanged -= self._onVehicleChanged
        self.__hangarSpace.onVehicleChangeStarted -= self._onVehicleChangeStarted
        self._clear()
        self._hitsPanel = None

    def _update(self):
        # A hit is chosen: drawn at once when the hangar shows its vehicle, else when the hangar has loaded it.
        battle, side, hit = self._hitsPanel.selection
        vehicle = hitsVehicle(battle, side, hit)
        target = (vehicle, hit) if hit is not None and hit.points and isinstance(vehicle, tuple) else None
        _logger.info('scene: hit lines: selection battle %s, side %s, hit at %s with %d points, vehicle %s; %s',
                     battle.battleId if battle is not None else None, side, hit.time if hit is not None else None,
                     len(hit.points) if hit is not None else 0, vehicle[0] if isinstance(vehicle, tuple) else vehicle,
                     'same target' if target == self._target else 'new target')
        if target == self._target:
            return
        self._target = target
        self._clear()
        if target is not None:
            self._draw('hit chosen')

    def _onVehicleChangeStarted(self, *args):
        self._clear()

    def _onVehicleChanged(self, *args):
        if self._target is not None:
            self._clear()
            self._draw('vehicle loaded')

    def _hangarModel(self):
        # (compound model, collisions) of the hangar vehicle when it is the vehicle of the hit and has loaded.
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
        hangarModel = self._hangarModel()
        if hangarModel is None:
            _logger.info('scene: hit lines: %s, not the vehicle of the hit yet: %s', reason, sceneState())
            return
        try:
            self._drawOn(reason, *hangarModel)
        except Exception:
            _logger.exception('hit lines: cannot draw')

    def _drawOn(self, reason, compoundModel, collisions):
        hit = self._target[1]
        points = []
        for point in hit.points:
            start, end = Math.Vector3(*point.start), Math.Vector3(*point.end)
            matrix = _partNode(compoundModel, point.part)
            if matrix is None or (end - start).length < 1e-6:
                continue
            points.append((point, matrix, matrix.applyPoint((start + end) * 0.5),
                           _unit(matrix.applyVector(end - start))))
        if hit.shellType == SHELL_TYPES.HIGH_EXPLOSIVE:
            points = points[:1]
        if not points:
            _logger.info('scene: hit lines: %s, no points on the vehicle', reason)
            return
        pieces = [(points[0][2] - points[0][3] * _LEAD, points[0][2])]
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
                elif self._normalTries < _NORMAL_TRIES:
                    self._normalTries += 1
                    self._callbackID = BigWorld.callback(_NORMAL_RETRY, self._onNormalRetry)
        spaceID = self.__hangarSpace.spaceID
        for start, end in pieces:
            self._addSegment(start, end, spaceID)
        hull = _partNode(compoundModel, TankPartIndexes.HULL)
        _logger.info('scene: hit lines: %s: %d pieces, %d models, first point %s, direction %s, hull node %s', reason,
                     len(pieces), len(self._models), _text(points[0][2]), _text(points[0][3]),
                     _text(hull.translation) if hull is not None else None)

    def _onNormalRetry(self):
        self._callbackID = None
        _logger.info('scene: hit lines: again for the ricochet normal (%d)', self._normalTries)
        self._removeModels()
        self._draw('ricochet normal')

    def _addSegment(self, start, end, spaceID):
        length = (end - start).length
        if length < 1e-4:
            return
        direction = (end - start) * (1.0 / length)
        dashes = int(math.ceil(length / _DASH - 1e-6))
        for index in range(dashes):
            dashStart = start + direction * (index * _DASH)
            dashEnd = start + direction * min(length, (index + 1) * _DASH)
            if (dashEnd - dashStart).length < 1e-4:
                continue
            model = BigWorld.Model(_DASH_LINES[index % len(_DASH_LINES)])
            model.addMotor(BigWorld.Servo(_segmentMatrix(dashStart, dashEnd, _THICKNESS)))
            model.castsShadow = False
            BigWorld.addModel(model, spaceID)
            model.visible = True
            self._models.append(model)

    def _clear(self):
        # Removes the lines and forgets the drawing that waits for the collision model.
        if self._callbackID is not None:
            BigWorld.cancelCallback(self._callbackID)
            self._callbackID = None
        self._normalTries = 0
        self._removeModels()

    def _removeModels(self):
        if self._models:
            _logger.info('scene: hit lines: remove %d models', len(self._models))
        for model in self._models:
            try:
                if model in BigWorld.models():
                    BigWorld.delModel(model)
            except Exception:
                _logger.exception('hit lines: cannot remove a model')
        self._models = []
