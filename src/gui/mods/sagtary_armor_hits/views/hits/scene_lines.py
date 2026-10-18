# -*- coding: utf-8 -*-
"""Scene lines: dashed tubes in the 3D scene, drawn with the client's debug drawer.

The client's armor overlay (armor_inspector) colors the vehicle after the scene's models, so it covers any model, with
any shader. The client's debug drawer (the native DebugDrawer module, used by the hangar camera alignment tools)
draws in a pass of its own after it, so its shapes stay over the overlay; tested against the scene's depth (zTest),
they are still hidden behind the vehicle. A line is a cylinder between two points, _RADIUS thick
(DebugDrawer.DebugDrawer().cylinder()). Its shapes last one frame, so SceneLines draws them again on every frame
(BigWorld.callback) while it has pieces.

A piece is dashed in its colors in turn, _DASH metres a dash from its start; a piece of one color is solid.
"""
import logging
import math

import BigWorld

_logger = logging.getLogger('sagtary.armor_hits')

# Metres: the length of a dash, the radius of a line.
_DASH = 0.1
_RADIUS = 0.009


def _cylinder(builder, start, end):
    # The cylinder builder takes its end points either as two vectors or as a list of them.
    try:
        return builder.endPoints(start, end)
    except TypeError:
        return builder.endPoints([start, end])


class SceneLines(object):

    def __init__(self):
        # [(start, end, argb)]: the dashes to draw.
        self._dashes = []
        self._callbackID = None

    def __len__(self):
        return len(self._dashes)

    def add(self, start, end, colours):
        # A piece of a way: dashed in the colors (ARGB) in turn, solid in one color.
        length = (end - start).length
        if length < 1e-4:
            return
        if len(colours) == 1:
            self._dashes.append((start, end, colours[0]))
        else:
            direction = (end - start) * (1.0 / length)
            for index in range(int(math.ceil(length / _DASH - 1e-6))):
                dashStart = start + direction * (index * _DASH)
                dashEnd = start + direction * min(length, (index + 1) * _DASH)
                if (dashEnd - dashStart).length >= 1e-4:
                    self._dashes.append((dashStart, dashEnd, colours[index % len(colours)]))
        if self._callbackID is None:
            self._callbackID = BigWorld.callback(0.0, self._onFrame)

    def clear(self):
        self._dashes = []
        if self._callbackID is not None:
            BigWorld.cancelCallback(self._callbackID)
            self._callbackID = None

    def _onFrame(self):
        self._callbackID = None
        if not self._dashes:
            return
        try:
            import DebugDrawer
            for start, end, colour in self._dashes:
                _cylinder(DebugDrawer.DebugDrawer().cylinder().zTest(True).colour(colour), start, end).radius(_RADIUS)
        except Exception:
            _logger.exception('scene lines: cannot draw')
            return
        self._callbackID = BigWorld.callback(0.0, self._onFrame)
