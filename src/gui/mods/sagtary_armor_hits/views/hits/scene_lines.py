# -*- coding: utf-8 -*-
"""Scene lines: shapes in the 3D scene, drawn with the client's debug drawer.

The client's armor overlay (armor_inspector) colors the vehicle after the scene's models, so it covers any model, with
any shader. The client's debug drawer (the native DebugDrawer module, used by the hangar camera alignment tools)
draws in a pass of its own after it, so its shapes stay over the overlay; tested against the scene's depth (zTest),
they are still hidden behind the vehicle. Its shapes last one frame, so SceneLines draws them again on every frame
(BigWorld.callback) while it has some.

The debug drawer has cylinders and spheres; SceneLines builds the others from cylinders: a dashed tube (dashes of
_DASH metres in colors in turn, or gaps) and a ring (a circle of short cylinders around an axis).
"""
import logging
import math

import BigWorld
import Math

_logger = logging.getLogger('sagtary.armor_hits')

# Metres: the length of a dash. The pieces of a ring.
_DASH = 0.1
_RING_STEPS = 40


def _cylinder(builder, start, end):
    # The cylinder builder takes its end points either as two vectors or as a list of them.
    try:
        return builder.endPoints(start, end)
    except TypeError:
        return builder.endPoints([start, end])


def _unit(vector):
    vector = Math.Vector3(vector)
    vector.normalise()
    return vector


def _cross(a, b):
    return Math.Vector3(a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x)


def _basis(axis):
    # Two unit vectors square to the axis and to each other.
    other = Math.Vector3(0.0, 1.0, 0.0) if abs(axis.y) < 0.9 else Math.Vector3(1.0, 0.0, 0.0)
    first = _unit(_cross(axis, other))
    return first, _cross(axis, first)


def ringPoints(centre, axis, ringRadius, count):
    # count points evenly round a circle of ringRadius around the axis through the centre, the first on the same side
    # for every circle of the axis.
    first, second = _basis(_unit(axis))
    return [centre + (first * math.cos(angle) + second * math.sin(angle)) * ringRadius
            for angle in (2.0 * math.pi * index / count for index in range(count))]


class SceneLines(object):

    def __init__(self):
        # [(kind, ...)]: the shapes to draw: ('tube', start, end, argb, radius), ('sphere', centre, size, argb,
        # wireframe).
        self._shapes = []
        self._callbackID = None

    def __len__(self):
        return len(self._shapes)

    def tube(self, start, end, colour, radius):
        if (end - start).length >= 1e-4:
            self._shapes.append(('tube', Math.Vector3(start), Math.Vector3(end), colour, radius))
            self._start()

    def dashed(self, start, end, colours, radius):
        # Dashes in the colors in turn from the start, None a gap; one color is a solid tube.
        length = (end - start).length
        if length < 1e-4:
            return
        if len(colours) == 1:
            self.tube(start, end, colours[0], radius)
            return
        direction = (end - start) * (1.0 / length)
        for index in range(int(math.ceil(length / _DASH - 1e-6))):
            colour = colours[index % len(colours)]
            if colour is not None:
                self.tube(start + direction * (index * _DASH), start + direction * min(length, (index + 1) * _DASH),
                          colour, radius)

    def sphere(self, centre, size, colour, wireframe=False):
        self._shapes.append(('sphere', Math.Vector3(centre), size, colour, wireframe))
        self._start()

    def ring(self, centre, axis, ringRadius, colour, radius):
        # A circle of ringRadius around the axis through the centre.
        points = ringPoints(centre, axis, ringRadius, _RING_STEPS)
        for start, end in zip(points, points[1:] + points[:1]):
            self.tube(start, end, colour, radius)

    def clear(self):
        self._shapes = []
        if self._callbackID is not None:
            BigWorld.cancelCallback(self._callbackID)
            self._callbackID = None

    def _start(self):
        if self._callbackID is None:
            self._callbackID = BigWorld.callback(0.0, self._onFrame)

    def _onFrame(self):
        self._callbackID = None
        if not self._shapes:
            return
        try:
            import DebugDrawer
            for shape in self._shapes:
                if shape[0] == 'tube':
                    _, start, end, colour, radius = shape
                    builder = DebugDrawer.DebugDrawer().cylinder().zTest(True).colour(colour)
                    _cylinder(builder, start, end).radius(radius)
                else:
                    _, centre, size, colour, wireframe = shape
                    builder = DebugDrawer.DebugDrawer().sphere().zTest(True).wireframe(wireframe).colour(colour)
                    builder.position(centre).scale(Math.Vector3(size, size, size))
        except Exception:
            _logger.exception('scene lines: cannot draw')
            return
        self._callbackID = BigWorld.callback(0.0, self._onFrame)
