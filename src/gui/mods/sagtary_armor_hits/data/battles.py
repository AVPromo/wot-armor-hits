# -*- coding: utf-8 -*-
"""Battles of the current game session: the data of the hits screen's battle selector.

- Battle: what is known about one battle, read from the client when the battle starts. New fields are added with a
  default value in FIELDS, so the code that makes or reads a Battle keeps working.
- BattleStore: the battles of this session in memory, newest first, up to BATTLES_LIMIT; nothing is saved to disk.
  It tells its listeners when the list changes (onChanged).
- BattleCollector: adds a Battle to the store when the player enters a battle or starts a replay.
"""
import logging
import time

import BattleReplay
import BigWorld
from Event import Event
from PlayerEvents import g_playerEvents

from gui.mods.sagtary_armor_hits.config import BATTLES_LIMIT

_logger = logging.getLogger('sagtary.armor_hits')


class Battle(object):
    # Field name and its default value. The order is the order of the constructor arguments.
    FIELDS = (
        ('arenaUniqueID', 0),       # id of the battle on the server; unique, the key of the battle
        ('arenaTypeID', 0),         # map and gameplay type
        ('geometryName', ''),       # map folder name, e.g. '05_prohorovka'; names the map images
        ('mapName', ''),            # map name in the client language
        ('arenaGuiType', 0),        # constants.ARENA_GUI_TYPE: random, training, ...
        ('arenaBonusType', 0),      # constants.ARENA_BONUS_TYPE
        ('vehicleCompactDescr', 0), # the player's vehicle type (intCD)
        ('vehicleName', ''),        # the player's vehicle short name in the client language
        ('startTime', 0.0),         # when the client entered the battle, Unix time
        ('isReplay', False),        # a replay played back, not a battle
    )
    __slots__ = tuple(name for name, _ in FIELDS)

    def __init__(self, **values):
        unknown = set(values) - set(self.__slots__)
        if unknown:
            raise TypeError('unknown Battle fields: %s' % ', '.join(sorted(unknown)))
        for name, default in self.FIELDS:
            setattr(self, name, values.get(name, default))

    @property
    def battleID(self):
        return self.arenaUniqueID

    def replace(self, **values):
        data = self.toDict()
        data.update(values)
        return Battle(**data)

    def toDict(self):
        return dict((name, getattr(self, name)) for name, _ in self.FIELDS)

    def __eq__(self, other):
        return isinstance(other, Battle) and self.toDict() == other.toDict()

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return 'Battle(%s)' % ', '.join('%s=%r' % (name, getattr(self, name)) for name, _ in self.FIELDS)


def battleFromAvatar(player):
    # The battle the player has just entered, read from the client.
    arena = player.arena
    arenaType = arena.arenaType if arena is not None else None
    descriptor = getattr(player, 'vehicleTypeDescriptor', None)
    if descriptor is None and arena is not None:
        descriptor = (arena.vehicles.get(player.playerVehicleID) or {}).get('vehicleType')
    vehicleType = descriptor.type if descriptor is not None else None
    return Battle(
        arenaUniqueID=player.arenaUniqueID,
        arenaTypeID=player.arenaTypeID,
        geometryName=getattr(arenaType, 'geometryName', ''),
        mapName=getattr(arenaType, 'name', ''),
        arenaGuiType=player.arenaGuiType,
        arenaBonusType=player.arenaBonusType,
        vehicleCompactDescr=vehicleType.compactDescr if vehicleType is not None else 0,
        vehicleName=vehicleType.shortUserString if vehicleType is not None else '',
        startTime=time.time(),
        isReplay=BattleReplay.isPlaying(),
    )


class BattleStore(object):

    def __init__(self, limit=BATTLES_LIMIT):
        self._limit = limit
        self._battles = []
        self.onChanged = Event()

    def getBattles(self):
        # Newest first.
        return list(self._battles)

    def getBattle(self, battleID):
        for battle in self._battles:
            if battle.battleID == battleID:
                return battle
        return None

    def add(self, battle):
        # A battle with the same id (a reconnect to the same battle) is replaced and moves to the top.
        self._battles = [item for item in self._battles if item.battleID != battle.battleID]
        self._battles.insert(0, battle)
        del self._battles[self._limit:]
        self.onChanged()

    def clear(self):
        self._battles = []
        self.onChanged()


class BattleCollector(object):

    def __init__(self, store):
        self._store = store

    def install(self):
        g_playerEvents.onAvatarReady += self._onAvatarReady

    def uninstall(self):
        g_playerEvents.onAvatarReady -= self._onAvatarReady

    def _onAvatarReady(self):
        try:
            battle = battleFromAvatar(BigWorld.player())
        except Exception:
            _logger.exception('battles: cannot read the battle')
            return
        self._store.add(battle)
        _logger.info('battles: %s, %s, %s', battle.battleID, battle.geometryName, battle.vehicleName)
