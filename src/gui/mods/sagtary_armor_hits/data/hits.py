# -*- coding: utf-8 -*-
"""Hits of a battle: the shells that hit the player's vehicle and the shells the player hit other vehicles with.

- Hit: one hit, read from the client when the server tells about it (Vehicle.showDamageFromShot for a shell that hit,
  Vehicle.showDamageFromExplosion for a high explosive splash). It keeps what the server sent; its result is worked
  out from that, like in the client's damage log: damage, a critical hit without damage, or blocked.
- HitCollector: adds the hits of the battle the player is in to its Battle in the BattleStore: receivedHits (the
  player's vehicle was hit) and dealtHits (the player's vehicle hit another one). The client knows the hits on the
  vehicles it sees, so all the player's hits are there, and the hits on the player's vehicle. The client's battle
  events (PlayerAvatar.onBattleEvents, the source of its damage log) add the crits, a premium shell and the blocked
  damage to the hit of the same vehicle that comes within _PAIRING_TIME before or after.
"""
import logging

import BigWorld
from Avatar import PlayerAvatar
from BattleFeedbackCommon import BATTLE_EVENT_TYPE
from constants import ARENA_PERIOD, SHELL_TYPES, SHELL_TYPES_LIST, VEHICLE_HIT_EFFECT
from PlayerEvents import g_playerEvents
from Vehicle import Vehicle
from VehicleEffects import DamageFromShotDecoder

from gui.mods.sagtary_armor_hits.data.record import Record

_logger = logging.getLogger('sagtary.armor_hits')


class HitResult(object):
    # The hit's result, like the icons of the client's damage log.
    DAMAGE = 'damage'
    CRITICAL = 'critical'
    BLOCKED = 'blocked'
    ALL = (DAMAGE, CRITICAL, BLOCKED)


_CRITICAL_EFFECTS = (VEHICLE_HIT_EFFECT.CRITICAL_HIT, VEHICLE_HIT_EFFECT.ARMOR_PIERCED_DEVICE_DAMAGED)


class Hit(Record):
    FIELDS = (
        ('time', 0.0),          # seconds since the battle started (the arena's battle period)
        ('vehicleId', 0),       # the other vehicle (intCD): the shooter of a received hit, the target of a dealt one
        ('playerName', ''),     # the other vehicle's player
        ('shellType', ''),      # the shell kind, a constants.SHELL_TYPES name: ARMOR_PIERCING, HIGH_EXPLOSIVE, ...
        ('damage', 0),          # hit points the hit took
        ('blockedDamage', 0),   # damage the armor blocked (received hits only, as the client tells it)
        ('hitEffects', ()),     # constants.VEHICLE_HIT_EFFECT of each point the shell hit, in order
        ('isSplash', False),    # a high explosive splash nearby, not a hit on the armor
        ('critsCount', 0),      # modules and crew the hit damaged, as the client's damage log counts them
        ('isGoldShell', False), # a premium shell
    )
    __slots__ = tuple(name for name, _ in FIELDS)

    @property
    def result(self):
        if self.damage > 0:
            return HitResult.DAMAGE
        if any(effect in _CRITICAL_EFFECTS for effect in self.hitEffects):
            return HitResult.CRITICAL
        return HitResult.BLOCKED


def _shellType(index):
    # SHELL_TYPES_LIST index of a decoded hit point, as the shell kind name.
    return SHELL_TYPES_LIST[index] if 0 <= index < len(SHELL_TYPES_LIST) else ''


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
# The server tells the event and the client shows the shell hit at about the same time, either one first (the hit
# waits for the shell's flight): an event and a hit of the same vehicle within this many seconds are one hit.
_PAIRING_TIME = 1.5


def _eventInfo(eventType, details):
    # {Hit field: value} of a battle event: crits, a premium shell, the damage the armor blocked.
    if eventType in _CRIT_EVENTS:
        critsCount, _, _, isGold = BATTLE_EVENT_TYPE.unpackCrits(details)[:4]
        return {'critsCount': critsCount, 'isGoldShell': bool(isGold)}
    damage, _, _, _, isGold = BATTLE_EVENT_TYPE.unpackDamage(details)[:5]
    info = {'isGoldShell': bool(isGold)}
    if eventType == BATTLE_EVENT_TYPE.TANKING:
        info['blockedDamage'] = damage
    return info


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
        else:
            hit = Hit(shellType=SHELL_TYPES.HIGH_EXPLOSIVE, damage=_argument(args, kwargs, 3, 'damage') or 0,
                      isSplash=True)
        arenaVehicle = player.arena.vehicles.get(otherID) or {}
        descriptor = arenaVehicle.get('vehicleType')
        hit = hit.replace(time=_battleTime(player.arena), playerName=arenaVehicle.get('name') or '',
                          vehicleId=descriptor.type.compactDescr if descriptor is not None else 0)
        key, now = (field, otherID), BigWorld.serverTime()
        for eventTime, info in self._pendingEvents.pop(key, ()):
            if now - eventTime <= _PAIRING_TIME:
                hit = hit.replace(**info)
        hits = getattr(battle, field) + (hit,)
        self._lastHits[key] = (now, battle.battleId, len(hits) - 1)
        self._store.update(battle.replace(**{field: hits}))

    @staticmethod
    def _shotHit(vehicle, args, kwargs):
        hitPoints = _argument(args, kwargs, 1, 'hitPoints') or ()
        collisions = vehicle.appearance.collisions if getattr(vehicle, 'appearance', None) is not None else None
        effects, shellType = [], ''
        if collisions is not None:
            for hitPoint in hitPoints:
                parsed = DamageFromShotDecoder.parseHitPoint(hitPoint, collisions)
                if parsed is not None:
                    effects.append(parsed[1])
                    shellType = shellType or _shellType(parsed[5])
        return Hit(damage=_argument(args, kwargs, 4, 'damage') or 0, shellType=shellType, hitEffects=tuple(effects))

    def _onBattleEvents(self, name, avatar, args, kwargs):
        now = BigWorld.serverTime()
        for event in _argument(args, kwargs, 0, 'events') or ():
            field = _EVENT_SIDES.get(event['eventType'])
            if field is None:
                continue
            key, info = (field, event['targetID']), _eventInfo(event['eventType'], event['details'])
            last = self._lastHits.get(key)
            battle = self._store.getBattle(last[1]) if last is not None and now - last[0] <= _PAIRING_TIME else None
            if battle is None:
                self._pendingEvents.setdefault(key, []).append((now, info))
                continue
            hits, index = getattr(battle, field), last[2]
            hits = hits[:index] + (hits[index].replace(**info),) + hits[index + 1:]
            self._store.update(battle.replace(**{field: hits}))


def _argument(args, kwargs, index, name):
    if name in kwargs:
        return kwargs[name]
    return args[index] if len(args) > index else None
