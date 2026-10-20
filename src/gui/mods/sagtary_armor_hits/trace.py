# -*- coding: utf-8 -*-
"""Call counts and checks for the log: to find calls made more often than needed, and why a hit's numbers do not
match what the screen shows.

calls(name, details) logs a call with the prefix "calls:", its number and the milliseconds since the last call of the
same name; a quiet call (the armor tooltip's ticks, every shell hit in battle) is only counted. summary(title) logs
the counts since the last summary and starts again: the hits screen logs one when it opens (the battle's calls) and
one when it closes. The checks of a hit log with the prefix "check:" (shot_panel.py, hit_lines.py); hitText and
modulesText are their texts of a hit and of a vehicle's modules.
"""
import logging

import BigWorld

_logger = logging.getLogger('sagtary.armor_hits')

# {name: calls since the last summary}, {name: BigWorld.time() of the last call}
_counts = {}
_lastTimes = {}
# constants.VEHICLE_HIT_EFFECT names by their values.
_EFFECT_NAMES = {0: 'piercedNoDamage', 1: 'ricochet', 2: 'finalRicochet', 3: 'notPierced', 4: 'pierced',
                 5: 'critical', 6: 'piercedDeviceDamaged'}


def calls(name, details='', quiet=False):
    now = BigWorld.time()
    count = _counts.get(name, 0) + 1
    _counts[name] = count
    last = _lastTimes.get(name)
    _lastTimes[name] = now
    if quiet:
        return
    since = '+%.0f ms' % ((now - last) * 1000) if last is not None else 'first'
    _logger.info('calls: %s #%d (%s)%s', name, count, since, ': ' + details if details else '')


def summary(title):
    if _counts:
        _logger.info('calls: %s: %s', title, ', '.join('%s %d' % item for item in sorted(_counts.items())))
    _counts.clear()
    _lastTimes.clear()


def modulesText(descriptor):
    # The vehicle and its chassis, turret and gun names.
    if descriptor is None:
        return 'none'
    try:
        return '%s (chassis %s, turret %s, gun %s)' % (descriptor.type.name, descriptor.chassis.name,
                                                       descriptor.turret.name, descriptor.gun.name)
    except Exception:
        return 'unknown modules of %r' % descriptor


def effectsText(effects):
    return '[%s]' % ', '.join(_EFFECT_NAMES.get(effect, str(effect)) for effect in effects)


def hitText(hit):
    # All the hit's data as recorded.
    points = ', '.join('part %s %s %s-%s' % (point.part, _EFFECT_NAMES.get(point.effect, point.effect), point.start,
                                             point.end) for point in hit.points)
    devices = ', '.join('%s %s' % (device.extra or device.device, device.code) for device in hit.damagedDevices)
    return ('time %.2f, vehicle %s, player %s, shell %s%s, damage %s, blocked %s, crits %s, effects %s, splash %s, '
            'distance %s, descr %s, points [%s], devices [%s]') % (
        hit.time, hit.vehicleId, hit.playerName, hit.shellType, ' gold' if hit.isGoldShell else '', hit.damage,
        hit.blockedDamage, hit.critsCount, effectsText(hit.hitEffects), hit.isSplash, hit.distance,
        'yes' if hit.vehicleDescr else 'no', points, devices)
