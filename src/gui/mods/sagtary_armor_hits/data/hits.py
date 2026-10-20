# -*- coding: utf-8 -*-
"""Hits of a battle: the shells that hit the player's vehicle and the shells the player hit other vehicles with.

- Hit: one hit, read from the client when the server tells about it (Vehicle.showDamageFromShot for a shell that hit,
  Vehicle.showDamageFromExplosion for a high explosive splash). It keeps what the server sent; its result is worked
  out from that, like the client's armor tooltip tells a shot: damage, not pierced, a ricochet, or no damage.
- DamagedDevice: a module or a crew member of the player's vehicle a shell damaged, by the client's own names (its
  damage info code, the vehicle's extra and the device kind), so it can be shown in any way later. The client's
  numbers for them are not kept: the extra's index depends on the vehicle type, the code's on the client version.
- HitPoint: one point a shell hit (a shell that ricochets or goes through spaced armor hits more than one): the
  vehicle part and the shell's way through its armor, as the server sends it (DamageFromShotDecoder.parseHitPoint).
  The points are in the part's own space, so they are drawn on the same vehicle with the same modules, whatever the
  turret and the gun angles: the hit keeps the other vehicle's compact descriptor for that.
- HitCollector: adds the hits of the battle the player is in to its Battle in the BattleStore: receivedHits (the
  player's vehicle was hit) and dealtHits (the player's vehicle hit another one). The client knows the hits on the
  vehicles it sees, so all the player's hits are there, and the hits on the player's vehicle. The client's battle
  events (PlayerAvatar.onBattleEvents, the source of its damage log) add the crits, a premium shell and the blocked
  damage to the hit of the same vehicle that comes within _PAIRING_TIME before or after; the client's damage info
  of the player's vehicle (PlayerAvatar.showVehicleDamageInfo) adds the modules and crew the shell damaged, the same
  way. The client tells which modules it damaged only on the player's own vehicle. The distance is between the two
  vehicles when the hit comes, when the client sees the shooter. A splash keeps where the shell burst, in the hit
  vehicle's chassis space (like the points), even when it burst on the ground nearby.
"""
import logging

import BigWorld
import Math
from Avatar import PlayerAvatar
from BattleFeedbackCommon import BATTLE_EVENT_TYPE, NONE_SHELL_TYPE
from constants import ARENA_PERIOD, DAMAGE_INFO_CODES, SHELL_TYPES, SHELL_TYPES_LIST, VEHICLE_HIT_EFFECT
from items.vehicles import DEVICE_TANKMAN_NAMES_TO_VEHICLE_EXTRA_NAMES
from PlayerEvents import g_playerEvents
from Vehicle import Vehicle
from VehicleEffects import DamageFromShotDecoder
from vehicle_systems.tankStructure import TankPartIndexes, TankPartNames

from gui.mods.sagtary_armor_hits.data.record import Record
from gui.mods.sagtary_armor_hits.trace import calls, hitText

_logger = logging.getLogger('sagtary.armor_hits')


class HitResult(object):
    # The hit's result: damage, then the results of the client's armor tooltip for a hit without damage (the armor
    # stopped the shell, the shell ricocheted, the shell pierced the armor but did no damage).
    DAMAGE = 'damage'
    BLOCKED = 'blocked'
    RICOCHET = 'ricochet'
    NO_DAMAGE = 'noDamage'
    ALL = (DAMAGE, BLOCKED, RICOCHET, NO_DAMAGE)


# Decimals of the hit point coordinates in metres: the server sends them to about 1 cm.
_POINT_DECIMALS = 3


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


def _shellType(index):
    # SHELL_TYPES_LIST index of a decoded hit point, as the shell kind name.
    return SHELL_TYPES_LIST[index] if 0 <= index < len(SHELL_TYPES_LIST) else ''


def vehicleDescr(descriptor):
    # The compact descriptor of a vehicle descriptor (its type and modules) as hex, '' without one.
    if descriptor is None:
        return ''
    try:
        return descriptor.makeCompactDescr().encode('hex')
    except Exception:
        _logger.exception('hits: no compact descriptor of %s', descriptor)
        return ''


def _vector(vector):
    return tuple(round(value, _POINT_DECIMALS) for value in (vector.x, vector.y, vector.z))


def _chassisPoint(vehicle, point):
    # A point of the scene in the vehicle's chassis space (the node the client puts the chassis hit effects on, else
    # the vehicle's own matrix), () when not known.
    try:
        nodeName = TankPartNames.getActualNodeNameByPartName(TankPartNames.CHASSIS)
        matrix = Math.Matrix(vehicle.appearance.compoundModel.node(nodeName))
    except Exception:
        try:
            matrix = Math.Matrix(vehicle.matrix)
        except Exception:
            _logger.debug('hits: no matrix of vehicle %s', vehicle.id, exc_info=True)
            return ()
    matrix.invert()
    return _vector(matrix.applyPoint(Math.Vector3(point)))


def _battleTime(arena):
    # Seconds since the battle period started; 0 before it.
    if arena is None or arena.period != ARENA_PERIOD.BATTLE:
        return 0.0
    return max(0.0, BigWorld.serverTime() - (arena.periodEndTime - arena.periodLength))


# The client's battle events (BattleFeedbackCommon.BATTLE_EVENT_TYPE) that tell more about a hit: the side of the
# hit; the event's targetID is the other vehicle (the target of the player's hit, the attacker of a received one).
_EVENT_SIDES = {
    BATTLE_EVENT_TYPE.DAMAGE: 'dealtHits',
    BATTLE_EVENT_TYPE.CRIT: 'dealtHits',
    BATTLE_EVENT_TYPE.RECEIVED_DAMAGE: 'receivedHits',
    BATTLE_EVENT_TYPE.RECEIVED_CRIT: 'receivedHits',
    BATTLE_EVENT_TYPE.TANKING: 'receivedHits',
}
_CRIT_EVENTS = (BATTLE_EVENT_TYPE.CRIT, BATTLE_EVENT_TYPE.RECEIVED_CRIT)
# The client's damage info codes of a shell have this in their names (DEVICE_CRITICAL_AT_SHOT, DEATH_FROM_SHOT, ...).
_SHOT_CODE = 'SHOT'
# {vehicle extra name: device or crew kind}
_EXTRA_DEVICES = dict((extra, device) for device, extras in DEVICE_TANKMAN_NAMES_TO_VEHICLE_EXTRA_NAMES.items()
                      for extra in extras)
# The server tells the event and the client shows the shell hit at about the same time, either one first (the hit
# waits for the shell's flight): an event and a hit of the same vehicle within this many seconds are one hit.
_PAIRING_TIME = 1.5


def _withInfo(hit, info):
    # The hit with the info of an event: the damaged devices are added to those it has, the others replaced.
    devices = info.get('damagedDevices')
    if devices:
        info = dict(info, damagedDevices=hit.damagedDevices + devices)
    return hit.replace(**info)


def _distance(vehicleID, otherID):
    # Metres between two vehicles the client sees, 0 when it does not see one of them.
    vehicle, other = BigWorld.entities.get(vehicleID), BigWorld.entities.get(otherID)
    if vehicle is None or other is None:
        return 0.0
    return round((vehicle.position - other.position).length, 1)


def _eventInfo(eventType, details):
    # {Hit field: value} of a battle event: crits, a premium shell, the damage the armor blocked. The events of the
    # player's own hits do not tell the shell (NONE_SHELL_TYPE): no premium flag from them.
    if eventType in _CRIT_EVENTS:
        critsCount, _, shellTypeID, isGold = BATTLE_EVENT_TYPE.unpackCrits(details)[:4]
        info = {'critsCount': critsCount}
    else:
        damage, _, _, shellTypeID, isGold = BATTLE_EVENT_TYPE.unpackDamage(details)[:5]
        info = {'blockedDamage': damage} if eventType == BATTLE_EVENT_TYPE.TANKING else {}
    if shellTypeID != NONE_SHELL_TYPE:
        info['isGoldShell'] = bool(isGold)
    return info


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


class HitCollector(object):

    def __init__(self, store):
        self._store = store
        # {(class, method name): original function}
        self._originals = {}
        # {(side field, other vehicle id): (server time, battle id, hit index)}: the last hit, for the events after it.
        self._lastHits = {}
        # {(side field, other vehicle id): [(server time, info)]}: events that came before their hit.
        self._pendingEvents = {}

    def install(self):
        for name in ('showDamageFromShot', 'showDamageFromExplosion'):
            self._wrap(Vehicle, name, self._onVehicleHit)
        self._wrap(PlayerAvatar, 'onBattleEvents', self._onBattleEvents)
        self._wrap(PlayerAvatar, 'showVehicleDamageInfo', self._onDamageInfo)
        g_playerEvents.onAvatarBecomeNonPlayer += self._reset

    def uninstall(self):
        g_playerEvents.onAvatarBecomeNonPlayer -= self._reset
        for (cls, name), original in self._originals.items():
            setattr(cls, name, original)
        self._originals = {}
        self._reset()

    def _reset(self, *args):
        self._lastHits = {}
        self._pendingEvents = {}

    def _wrap(self, cls, name, handler):
        if name not in cls.__dict__:
            _logger.warning('hits: %s.%s not in this client', cls.__name__, name)
            return
        original = cls.__dict__[name]

        def wrapper(entity, *args, **kwargs):
            try:
                calls('hits: %s' % name, quiet=True)
                handler(name, entity, args, kwargs)
            except Exception:
                _logger.exception('hits: cannot read %s.%s', cls.__name__, name)
            return original(entity, *args, **kwargs)

        wrapper.__name__ = name
        self._originals[(cls, name)] = original
        setattr(cls, name, wrapper)

    def _onVehicleHit(self, name, vehicle, args, kwargs):
        player = BigWorld.player()
        playerVehicleID = getattr(player, 'playerVehicleID', None)
        attackerID = _argument(args, kwargs, 0, 'attackerID')
        if vehicle.id == playerVehicleID:
            field, otherID = 'receivedHits', attackerID
        elif attackerID == playerVehicleID:
            field, otherID = 'dealtHits', vehicle.id
        else:
            return
        battle = self._store.getBattle(player.arenaUniqueID)
        if battle is None:
            return
        if name == 'showDamageFromShot':
            hit = self._shotHit(vehicle, args, kwargs)
            if field == 'dealtHits':
                hit = hit.replace(isGoldShell=self._ownShellIsGold(player, hit.shellType))
        else:
            center = _argument(args, kwargs, 1, 'center')
            hit = Hit(shellType=SHELL_TYPES.HIGH_EXPLOSIVE, damage=_argument(args, kwargs, 3, 'damage') or 0,
                      isSplash=True, splashCenter=_chassisPoint(vehicle, center) if center is not None else ())
        arenaVehicle = player.arena.vehicles.get(otherID) or {}
        descriptor = arenaVehicle.get('vehicleType')
        hit = hit.replace(time=_battleTime(player.arena), playerName=arenaVehicle.get('name') or '',
                          vehicleId=descriptor.type.compactDescr if descriptor is not None else 0,
                          vehicleDescr=vehicleDescr(descriptor), distance=_distance(vehicle.id, attackerID))
        key, now = (field, otherID), BigWorld.serverTime()
        for eventTime, info in self._pendingEvents.pop(key, ()):
            if now - eventTime <= _PAIRING_TIME:
                hit = _withInfo(hit, info)
        hits = getattr(battle, field) + (hit,)
        self._lastHits[key] = (now, battle.battleId, len(hits) - 1)
        _logger.info('hits: %s #%d of vehicle %s: %s', field, len(hits), otherID, hitText(hit))
        self._store.update(battle.replace(**{field: hits}))

    @staticmethod
    def _ownShellIsGold(player, shellType):
        # The player's shell of a dealt hit: the server does not tell whether it was a premium one.
        try:
            ammo = player.guiSessionProvider.shared.ammo
            isGold = ownShellIsGold(player.vehicleTypeDescriptor, shellType, ammo.getCurrentShellCD())
        except Exception:
            _logger.debug('hits: no shell of the player', exc_info=True)
            isGold = None
        return bool(isGold)

    @staticmethod
    def _shotHit(vehicle, args, kwargs):
        hitPoints = _argument(args, kwargs, 1, 'hitPoints') or ()
        collisions = vehicle.appearance.collisions if getattr(vehicle, 'appearance', None) is not None else None
        effects, points, shellType = [], [], ''
        if collisions is not None:
            for hitPoint in hitPoints:
                parsed = DamageFromShotDecoder.parseHitPoint(hitPoint, collisions)
                if parsed is None:
                    continue
                part, effect, start, end = parsed[:4]
                effects.append(effect)
                shellType = shellType or _shellType(parsed[5])
                # A dynamic part (negative index) is not one of the vehicle's own parts.
                if 0 <= part < len(TankPartIndexes.ALL):
                    points.append(HitPoint(part=part, start=_vector(start), end=_vector(end), effect=effect))
        return Hit(damage=_argument(args, kwargs, 4, 'damage') or 0, shellType=shellType, hitEffects=tuple(effects),
                   points=tuple(points))

    def _onBattleEvents(self, name, avatar, args, kwargs):
        for event in _argument(args, kwargs, 0, 'events') or ():
            field = _EVENT_SIDES.get(event['eventType'])
            if field is not None:
                self._addInfo((field, event['targetID']), _eventInfo(event['eventType'], event['details']))

    def _onDamageInfo(self, name, avatar, args, kwargs):
        # What a shell of the attacker (entityID) did to the player's vehicle: a module or a crew member damaged, a
        # fire, the vehicle destroyed. The extra index 0 is none.
        vehicleID, damageIndex = _argument(args, kwargs, 0, 'vehicleID'), _argument(args, kwargs, 1, 'damageIndex')
        extraIndex, attackerID = _argument(args, kwargs, 2, 'extraIndex'), _argument(args, kwargs, 3, 'entityID')
        if vehicleID != getattr(avatar, 'playerVehicleID', None):
            return
        code = DAMAGE_INFO_CODES[damageIndex]
        _logger.info('hits: damage info %s, extra %s, attacker %s', code, extraIndex, attackerID)
        if _SHOT_CODE not in code:
            return
        extra = avatar.vehicleTypeDescriptor.extras[extraIndex].name if extraIndex else ''
        device = DamagedDevice(code=code, extra=extra, device=_EXTRA_DEVICES.get(extra, ''))
        self._addInfo(('receivedHits', attackerID), {'damagedDevices': (device,)})

    def _addInfo(self, key, info):
        # Adds the info to the last hit of the key within _PAIRING_TIME, or keeps it for the hit to come.
        now = BigWorld.serverTime()
        last = self._lastHits.get(key)
        battle = self._store.getBattle(last[1]) if last is not None and now - last[0] <= _PAIRING_TIME else None
        if battle is None:
            _logger.info('hits: %s of vehicle %s waits for its hit: %s', key[0], key[1], info)
            self._pendingEvents.setdefault(key, []).append((now, info))
            return
        field = key[0]
        hits, index = getattr(battle, field), last[2]
        _logger.info('hits: %s #%d of vehicle %s gets %s', field, index + 1, key[1], info)
        hits = hits[:index] + (_withInfo(hits[index], info),) + hits[index + 1:]
        self._store.update(battle.replace(**{field: hits}))


def _argument(args, kwargs, index, name):
    if name in kwargs:
        return kwargs[name]
    return args[index] if len(args) > index else None
