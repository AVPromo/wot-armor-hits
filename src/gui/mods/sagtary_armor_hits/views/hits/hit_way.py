# -*- coding: utf-8 -*-
"""The look of a hit's way (hit_lines.Way) in the scene, drawn with the scene lines (scene_lines.py).

The way to the first point is a solid white tube; the way on after a ricochet or spaced armor is dashed in white with
gaps (white, nothing, white...). At the way's start, where nothing covers it, a white dot as wide as the way and
white rings square to the way, _RING_WIDTH times as thick as it: a cone with its tip on the start, the rings back
towards the shooter, each _CONE times its radius away (the outer ring the farthest), so that they look nested from
the shooter's side. The chosen hit has two rings and the way's full width, the other hits one ring and a thinner way.
A splash is a sphere of three rings around the vehicle's axes with the dot on the point where the shell burst, and a
dashed line from there down (or up) to the tracks' level, so that it shows whether the shell burst below or above the
vehicle. All in white.
"""
import Math

_WHITE = 0xFFFFFFFF
# Metres: the way's radius, the chosen hit's and the others'.
_RADIUS = 0.009
_OTHER_RADIUS = 0.006
# A ring's thickness by the way's; a start ring's distance back from the start by its radius; the start rings' radii
# in metres (the chosen hit's, the others').
_RING_WIDTH = 0.5
_CONE = 1.6
_START_RINGS = (0.08, 0.16)
_OTHER_START_RINGS = (0.1,)
# Metres: a splash sphere's radius (the chosen hit's, the others').
_SPHERE = 0.5
_OTHER_SPHERE = 0.3


def _unit(vector):
    vector = Math.Vector3(vector)
    vector.normalise()
    return vector


def drawWay(lines, way, chosen):
    # The way into the scene lines.
    radius = _RADIUS if chosen else _OTHER_RADIUS
    if way.lead is not None:
        start, end = way.lead
        direction = _unit(end - start)
        lines.tube(start, end, _WHITE, radius)
        for ringRadius in (_START_RINGS if chosen else _OTHER_START_RINGS):
            lines.ring(start - direction * (ringRadius * _CONE), direction, ringRadius, _WHITE, radius * _RING_WIDTH)
        lines.sphere(start, radius * 2.0, _WHITE)
    for start, end in way.links + ([way.out] if way.out is not None else []):
        lines.dashed(start, end, (_WHITE, None), radius)
    if way.splash is not None:
        centre, axes, foot = way.splash
        for axis in axes:
            lines.ring(centre, axis, _SPHERE if chosen else _OTHER_SPHERE, _WHITE, radius * _RING_WIDTH)
        lines.sphere(centre, radius * 2.0, _WHITE)
        if foot is not None:
            lines.dashed(centre, foot, (_WHITE, None), radius)
