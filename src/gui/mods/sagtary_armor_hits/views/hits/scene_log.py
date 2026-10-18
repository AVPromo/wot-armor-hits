# -*- coding: utf-8 -*-
"""Log of the hits screen's scene, while the way the hangar vehicle and the hit lines are updated is worked out.

SceneLog writes to the log, with the prefix "scene:", the client's events of the hangar vehicle (HangarSpace:
onVehicleChangeStarted, onVehicleChanged, onSpaceCreate; the preview vehicle: onSelected, onChanged), each with the
state of the hangar vehicle at that moment (sceneState). The presenters of the hangar vehicle and the hit lines log
what they ask for and what they draw with the same prefix.
"""
import logging

import BigWorld
import Math
from CurrentVehicle import g_currentPreviewVehicle
from helpers import dependency
from skeletons.gui.shared.utils import IHangarSpace

_logger = logging.getLogger('sagtary.armor_hits')


def _vector(vector):
    return '(%.2f, %.2f, %.2f)' % (vector.x, vector.y, vector.z)


def sceneState():
    # The hangar vehicle as text: model loaded, the entity's vehicle, its compound model, collisions, hull node place.
    hangarSpace = dependency.instance(IHangarSpace)
    if not hangarSpace.spaceInited:
        return 'space not inited'
    entity = hangarSpace.getVehicleEntity()
    if entity is None:
        return 'loaded %s, no entity' % hangarSpace.isModelLoaded
    descriptor = getattr(entity, 'typeDescriptor', None)
    appearance = getattr(entity, 'appearance', None)
    compoundModel = getattr(appearance, 'compoundModel', None) if appearance is not None else None
    collisions = getattr(appearance, 'collisions', None) if appearance is not None else None
    hull = None
    if compoundModel is not None:
        try:
            hull = _vector(Math.Matrix(compoundModel.node('hull')).translation)
        except Exception:
            hull = 'no node'
    return 'loaded %s, entity %s, vehicle %s, model %s, collisions %s, hull %s, preview %s, time %.2f' % (
        hangarSpace.isModelLoaded, entity.id, descriptor.type.compactDescr if descriptor is not None else None,
        '%x' % id(compoundModel) if compoundModel is not None else None, collisions is not None, hull,
        g_currentPreviewVehicle.intCD, BigWorld.time())


class SceneLog(object):
    __hangarSpace = dependency.descriptor(IHangarSpace)

    def init(self):
        _logger.info('scene: screen opened: %s', sceneState())
        self.__hangarSpace.onVehicleChangeStarted += self._onVehicleChangeStarted
        self.__hangarSpace.onVehicleChanged += self._onVehicleChanged
        self.__hangarSpace.onSpaceCreate += self._onSpaceCreate
        g_currentPreviewVehicle.onSelected += self._onPreviewSelected
        g_currentPreviewVehicle.onChanged += self._onPreviewChanged

    def fini(self):
        g_currentPreviewVehicle.onChanged -= self._onPreviewChanged
        g_currentPreviewVehicle.onSelected -= self._onPreviewSelected
        self.__hangarSpace.onSpaceCreate -= self._onSpaceCreate
        self.__hangarSpace.onVehicleChanged -= self._onVehicleChanged
        self.__hangarSpace.onVehicleChangeStarted -= self._onVehicleChangeStarted
        _logger.info('scene: screen closed: %s', sceneState())

    @staticmethod
    def _onVehicleChangeStarted(*args):
        _logger.info('scene: event onVehicleChangeStarted: %s', sceneState())

    @staticmethod
    def _onVehicleChanged(*args):
        _logger.info('scene: event onVehicleChanged: %s', sceneState())

    @staticmethod
    def _onSpaceCreate(*args):
        _logger.info('scene: event onSpaceCreate: %s', sceneState())

    @staticmethod
    def _onPreviewSelected(*args):
        _logger.info('scene: event preview onSelected: %s', sceneState())

    @staticmethod
    def _onPreviewChanged(*args):
        _logger.info('scene: event preview onChanged: %s', sceneState())
