# -*- coding: utf-8 -*-
"""Hits of a battle: the shells that hit the player's vehicle and the shells the player hit other vehicles with.

The hits' data, as the battle files keep it (Record); hit_parser.py makes them from the server's calls,
hit_collector.py in battle.

- Hit: one hit, read from the client when the server tells about it (Vehicle.showDamageFromShot for a shell that hit,
  Vehicle.showDamageFromExplosion for a high explosive splash). It keeps what the server sent; its result is worked
  out from that, like the client's armor tooltip tells a shot: damage, not pierced, a ricochet, or no damage.
- DamagedDevice: a module or a crew member of the player's vehicle a shell damaged, by the client's own names (its
  damage info code, the vehicle's extra and the device kind), so it can be shown in any way later. The client's
  numbers for them are not kept: the extra's index depends on the vehicle type, the code's on the client version.
- HitPoint: one point a shell hit (a shell that ricochets or goes through spaced armor hits more than one): the
  vehicle part and the shell's way through its armor, as the server sends it (DamageFromShotDecoder.parseHitPoint).
  The points are in the part's own space, so they are drawn on the same vehicle with the same modules, whatever the
  turret and the gun angles: the hit keeps the other vehicle's compact descriptor for that. The server packs a
  point to 1/255 of the part's size on each axis, so the direction along a short way is off by a degree or so: the
  hit keeps the shell's exact direction at its first point too (Hit.shotDirection), from the shell's tracer.
"""
import logging

from constants import VEHICLE_HIT_EFFECT

from gui.mods.sagtary_armor_hits.data.record import Record

_logger = logging.getLogger('sagtary.armor_hits')


class HitResult(object):
    # The hit's result: damage, then the results of the client's armor tooltip for a hit without damage (the armor
    # stopped the shell, the shell ricocheted, the shell pierced the armor but did no damage).
    DAMAGE = 'damage'
    BLOCKED = 'blocked'
    RICOCHET = 'ricochet'
    NO_DAMAGE = 'noDamage'
    ALL = (DAMAGE, BLOCKED, RICOCHET, NO_DAMAGE)


class HitPoint(Record):
    FIELDS = (
        ('part', 0),            # the vehicle part (tankStructure.TankPartIndexes: chassis 0, hull 1, turret 2, gun 3)
        ('start', ()),          # (x, y, z) of the shell's way before the armor, in metres in the part's space
        ('end', ()),            # (x, y, z) of the shell's way behind the armor
        ('effect', 0),          # constants.VEHICLE_HIT_EFFECT of the point
    )
    __slots__ = tuple(name for name, _ in FIELDS)


class DamagedDevice(Record):
    FIELDS = (
        ('code', ''),           # constants.DAMAGE_INFO_CODES name: DEVICE_CRITICAL_AT_SHOT, DEVICE_DESTROYED_AT_SHOT,
                                # TANKMAN_HIT_AT_SHOT, DEVICE_STARTED_FIRE_AT_SHOT, DEATH_FROM_SHOT, ...
        ('extra', ''),          # the vehicle's extra (its slot) the code is about: engineHealth, leftTrack0Health,
                                # gunner2Health, ...; '' for none
        ('device', ''),         # the extra's kind, an items.vehicles VEHICLE_DEVICE_TYPE_NAMES or VEHICLE_TANKMAN_TYPE_NAMES
                                # name: engine, track, gunner, ...; '' when it is not one
    )
    __slots__ = tuple(name for name, _ in FIELDS)


class Hit(Record):
    FIELDS = (
        ('time', 0.0),          # seconds since the battle started (the arena's battle period)
        ('vehicleId', 0),       # the other vehicle (intCD): the shooter of a received hit, the target of a dealt one
        ('vehicleDescr', ''),   # the other vehicle's compact descriptor (its modules), hex; '' when not known
        ('playerName', ''),     # the other vehicle's player
        ('shellType', ''),      # the shell kind, a constants.SHELL_TYPES name: ARMOR_PIERCING, HIGH_EXPLOSIVE, ...
        ('damage', 0),          # hit points the hit took
        ('blockedDamage', 0),   # damage the armor blocked (received hits only, as the client tells it)
        ('hitEffects', ()),     # constants.VEHICLE_HIT_EFFECT of each point the shell hit, in order
        ('isSplash', False),    # a high explosive splash nearby, not a hit on the armor
        ('critsCount', 0),      # modules and crew the hit damaged, as the client's damage log counts them
        ('isGoldShell', False), # a premium shell
        ('points', ()),         # the points the shell hit, in order (HitPoint); none for a splash
        ('distance', 0.0),      # metres between the shooter and the target at the hit; 0 when not known
        ('damagedDevices', ()), # what the shell did to the player's vehicle (received hits), in order (DamagedDevice)
        ('splashCenter', ()),   # (x, y, z) where a splash's shell burst, in metres in the hit vehicle's chassis space
                                # (part 0 of the points); () when not known
        ('shotDirection', ()),  # (x, y, z) unit direction of the shell at the first point, in that point's part space,
                                # from the shell's tracer (exact, unlike the points); () when not known
    )
    NESTED = {'points': HitPoint, 'damagedDevices': DamagedDevice}
    __slots__ = tuple(name for name, _ in FIELDS)

    @property
    def result(self):
        # Without damage, the last point the shell hit tells what stopped it; a splash without damage is blocked.
        if self.damage > 0:
            return HitResult.DAMAGE
        last = self.hitEffects[-1] if self.hitEffects else VEHICLE_HIT_EFFECT.ARMOR_NOT_PIERCED
        if last in VEHICLE_HIT_EFFECT.RICOCHETS:
            return HitResult.RICOCHET
        if last in VEHICLE_HIT_EFFECT.PIERCED_HITS:
            return HitResult.NO_DAMAGE
        return HitResult.BLOCKED


def vehicleDescr(descriptor):
    # The compact descriptor of a vehicle descriptor (its type and modules) as hex, '' without one.
    if descriptor is None:
        return ''
    try:
        return descriptor.makeCompactDescr().encode('hex')
    except Exception:
        _logger.exception('hits: no compact descriptor of %s', descriptor)
        return ''


def ownShellIsGold(descriptor, shellType, currentShellCD=None):
    # Whether the player's shell of the kind is a premium one: the gun's only shell of the kind, else its current
    # shell when of the kind; None when not known.
    shells = [shot.shell for shot in descriptor.gun.shots if shot.shell.kind == shellType]
    if len(shells) == 1:
        return bool(shells[0].isGold)
    for shell in shells:
        if shell.compactDescr == currentShellCD:
            return bool(shell.isGold)
    return None
