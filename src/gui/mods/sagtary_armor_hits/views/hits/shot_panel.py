# -*- coding: utf-8 -*-
"""Shot panel of the hits screen, on the right: the chosen hit's shooter and target, its result and its numbers.

ShotPanelPresenter fills the view model (views/models/shot_panel_model.py) for the hit the hits panel has chosen:

- the cards of the shooter and the target: the player, the vehicle (the client's name, tier, icon and nation flag)
  with its modules of the battle (the compact descriptor); beside the shooter its gun and the shell of the hit,
  beside the target its turret when its type has more than one. On the received side the shooter is the other
  vehicle and the target the player's, on the dealt side the other way round;
- the hit's result icon (the hits panel's) and its number and battle time;
- the sections: damage (the hit's, the shell's average), penetration (the shell's, at the hit's distance when it is
  known), armor and impact angle (the vehicle's armor where the hit line meets it, counted in the garage like the
  client's armor tooltip does: getMaterialsAtCursor along the line, the shell's penetration chance there,
  calculatePenetrationInfo), distance (recorded in battle) and modules and crew (the damaged ones of the player's
  vehicle, as English text: the extra without 'Health', what the damage info code tells).

The shell is the overlay panel's (overlay_panel.py: the shooter's gun and shot with the hit's shell kind); the hit
line is the hit lines presenter's (hit_lines.py: its first point and direction when drawn). The armor needs the
vehicle's collision model, which comes a few frames after the vehicle: without it the armor is counted again after
_RETRY seconds, up to _TRIES times. A value counted in the garage is marked (counted) for the page.

Each fill logs its reason ("calls:") and what it shows the hit with ("check:"): the hit as recorded, the shell, the
hangar vehicle's modules against the hit's, the armor along the line; a "check: MISMATCH" line tells a number of the
hit that does not fit them (pierced with no chance in the garage, a damage far from the shell's, other modules).
"""
import logging
import math

import BigWorld
import nations
from helpers import dependency, int2roman
from helpers_common import computePiercingPowerAtDist
from items import parseIntCompactDescr, vehicles
from skeletons.gui.shared.utils import IHangarSpace

from gui.mods.sagtary_armor_hits.data.client_names import shownVehicleId, vehicleShortName
from gui.mods.sagtary_armor_hits.data.hits import HitResult
from gui.mods.sagtary_armor_hits.trace import calls, hitText, modulesText
from gui.mods.sagtary_armor_hits.views.hits.hangar_vehicle import hitsVehicle
from gui.mods.sagtary_armor_hits.views.hits.hits_panel import DEALT
from gui.mods.sagtary_armor_hits.views.models.shot_panel_model import ShotModuleModel, ShotRowModel, ShotSectionModel

_logger = logging.getLogger('sagtary.armor_hits')

_VEHICLE_ICON = 'img://gui/maps/icons/vehicle/%s.png'
_FLAG = 'img://gui/maps/icons/flags/160x100/%s.png'
_GUN_ICON = 'img://gui/maps/icons/modules/gun.png'
_TURRET_ICON = 'img://gui/maps/icons/modules/tower.png'
_SHELL_ICON = 'img://gui/maps/icons/shell/small/%s.png'
_NONE = u'—'
# English text of the damage info codes of a shell (data/hits.py DamagedDevice); another code is shown as it is.
_DEVICE_STATES = {
    'DEVICE_CRITICAL_AT_SHOT': 'critical',
    'DEVICE_DESTROYED_AT_SHOT': 'destroyed',
    'TANKMAN_HIT_AT_SHOT': 'wounded',
    'DEVICE_STARTED_FIRE_AT_SHOT': 'fire',
    'DEATH_FROM_DEVICE_EXPLOSION_AT_SHOT': 'exploded',
    'DEATH_FROM_INACTIVE_CREW_AT_SHOT': 'crew out',
    'DEATH_FROM_SHOT': 'vehicle destroyed',
}
_HEALTH_SUFFIX = 'Health'
# Metres of the hit line looked along for the armor: before and after its first point.
_RAY = 2.5
# The armor is counted again while the collision model has not come: seconds between, how many times.
_RETRY = 0.2
_TRIES = 5
# The VEHICLE_HIT_EFFECT values of a pierced armor and of a ricochet.
_PIERCED_EFFECTS = (0, 4, 5, 6)
_RICOCHET_EFFECTS = (1, 2)
# A shell's damage is its average within this part of it, both ways.
_DAMAGE_SPREAD = 0.25


def _time(seconds):
    seconds = int(seconds)
    return '%d:%02d' % (seconds // 60, seconds % 60)


def _descriptor(vehicleId, descr):
    # The vehicle descriptor with its modules (compact descriptor, hex), else with the default ones; None.
    try:
        if descr:
            return vehicles.VehicleDescr(compactDescr=descr.decode('hex'))
        nationID, typeID = parseIntCompactDescr(vehicleId)[1:]
        return vehicles.VehicleDescr(typeID=(nationID, typeID))
    except Exception:
        _logger.debug('shot panel: no descriptor of vehicle %s', vehicleId, exc_info=True)
        return None


def _vehicleImages(vehicleId):
    # (icon, flag) of the vehicle as the hangar shows it (a maps training copy as the vehicle it copies).
    try:
        vehicleType = vehicles.getVehicleType(shownVehicleId(vehicleId) or vehicleId)
        return _VEHICLE_ICON % vehicleType.name.replace(':', '-'), _FLAG % nations.NAMES[vehicleType.id[0]]
    except Exception:
        _logger.debug('shot panel: no images of vehicle %s', vehicleId, exc_info=True)
        return '', ''


def _materials(entity, start, end, shellParams):
    # ([material], penetration info) of the vehicle's armor along the segment, like the client's armor tooltip; None
    # when the collision model does not meet the segment (not loaded yet).
    from helpers.collisions import SegmentCollisionResultExt
    from shared_utils.vehicle_utils import getMatinfo
    from gui.impl.lobby.vehicle_hub.sub_presenters.armor.utils import getMaterialsAtCursor
    from gui.impl.lobby.vehicle_hub.sub_presenters.armor.penetration_utils import calculatePenetrationInfo
    collisions = getattr(entity.appearance, 'collisions', None)
    if collisions is None:
        _logger.info('check: armor: no collision model yet')
        return None
    found = collisions.collideAllWorld(start, end)
    _logger.info('check: armor: collisions along the line (distance, cos, material, part) %s; the hit point is at '
                 '%.2f', [(round(item[0], 3), round(item[1], 3), item[2], item[3]) for item in found or ()], _RAY)
    if not found or abs(found[0][0] - _RAY) > _RAY * 0.5:
        _logger.info('check: armor: the line MISSES the armor at the hit point (model not ready, other modules or '
                     'another vehicle?)')
        return None
    isWheeled = entity.typeDescriptor.type.isWheeledVehicle
    segments = [SegmentCollisionResultExt(distance, angleCos, getMatinfo(entity, part, kind, isWheeled), part)
                for distance, angleCos, kind, part in found]
    return getMaterialsAtCursor(entity, segments, shellParams), calculatePenetrationInfo(shellParams, segments)


class ShotPanelPresenter(object):
    __hangarSpace = dependency.descriptor(IHangarSpace)

    def __init__(self, model, hitsPanel, overlayPanel, hitLines, texts):
        # texts: the section titles, units and line labels in the client language (config TEXTS 'shot/*').
        self._model = model
        self._hitsPanel = hitsPanel
        self._overlayPanel = overlayPanel
        self._hitLines = hitLines
        self._texts = texts
        self._callbackID = None
        self._tries = 0
        # (battle id, side, number) of the hit last logged in full.
        self._checked = None

    def init(self):
        self._hitsPanel.onChanged += self._onHitsChanged
        self._hitLines.onDrawn += self._onLinesDrawn
        self._update('init')

    def fini(self):
        self._cancel()
        self._hitLines.onDrawn -= self._onLinesDrawn
        self._hitsPanel.onChanged -= self._onHitsChanged
        self._model = None
        self._hitsPanel = None
        self._overlayPanel = None
        self._hitLines = None

    def _cancel(self):
        if self._callbackID is not None:
            BigWorld.cancelCallback(self._callbackID)
            self._callbackID = None

    def _onRetry(self):
        self._callbackID = None
        self._fill('retry %d' % self._tries)

    def _onHitsChanged(self):
        self._update('hits panel changed')

    def _onLinesDrawn(self):
        self._update('hit lines drawn' if self._hitLines.chosenShot is not None else 'hit lines cleared')

    def _update(self, reason):
        self._cancel()
        self._tries = 0
        self._fill(reason)

    def _fill(self, reason):
        battle, side, hit = self._hitsPanel.selection
        calls('shot panel: fill', '%s; hit %s, line %s' % (reason, self._hitsPanel.selectedNumber,
                                                          self._hitLines.chosenShot is not None))
        if battle is None or hit is None:
            self._model.setIsVisible(False)
            return
        try:
            armor = self._armor(hit)
        except Exception:
            _logger.exception('shot panel: cannot count the armor')
            armor = None
        waits = armor is None and self._hitLines.chosenShot is not None and self._tries < _TRIES
        if waits:
            self._tries += 1
            self._callbackID = BigWorld.callback(_RETRY, self._onRetry)
        gunShot = self._overlayPanel.gunShot
        try:
            self._check(battle, side, hit, gunShot, armor, waits)
        except Exception:
            _logger.exception('shot panel: cannot check the hit')
        myName = getattr(BigWorld.player(), 'name', '') or ''
        if side == DEALT:
            shooter = (battle.vehicleId, battle.vehicleDescr, myName)
            target = (hit.vehicleId, hit.vehicleDescr, hit.playerName)
        else:
            shooter = (hit.vehicleId, hit.vehicleDescr, hit.playerName)
            target = (battle.vehicleId, battle.vehicleDescr, myName)
        with self._model.transaction() as model:
            model.setIsVisible(True)
            self._fillVehicle(model.shooter, self._texts['shooter'], shooter, self._shooterModules(gunShot))
            self._fillVehicle(model.target, self._texts['target'], target, self._targetModules(*target[:2]))
            model.setResultIcon('%s__%s' % (hit.result, side))
            model.setNumber(u'#%s · %s' % (self._hitsPanel.selectedNumber, _time(hit.time)))
            sections = model.getSections()
            sections.clear()
            for section in self._sections(hit, gunShot, armor):
                sections.addViewModel(section)
            sections.invalidate()

    @staticmethod
    def _fillVehicle(model, role, vehicle, modules):
        vehicleId, _, player = vehicle
        icon, flag = _vehicleImages(vehicleId)
        try:
            tier = int2roman(vehicles.getVehicleType(vehicleId).level)
        except Exception:
            tier = ''
        model.setRole(role)
        model.setPlayer(player or '')
        model.setVehicleName(vehicleShortName(vehicleId) or '')
        model.setTier(tier)
        model.setIcon(icon)
        model.setFlag(flag)
        array = model.getModules()
        array.clear()
        for moduleIcon, moduleTier, label in modules:
            item = ShotModuleModel()
            item.setIcon(moduleIcon)
            item.setTier(moduleTier)
            item.setLabel(label)
            array.addViewModel(item)
        array.invalidate()

    @staticmethod
    def _shooterModules(gunShot):
        # The shooter's gun and the hit's shell.
        if gunShot is None:
            return []
        gun, shot = gunShot
        return [(_GUN_ICON, int2roman(gun.level), gun.userString),
                (_SHELL_ICON % shot.shell.iconName, '', shot.shell.userString)]

    @staticmethod
    def _targetModules(vehicleId, descr):
        # The target's turret when its type has more than one to choose.
        descriptor = _descriptor(vehicleId, descr)
        if descriptor is None or len(descriptor.type.turrets[0]) < 2:
            return []
        turret = descriptor.turret
        return [(_TURRET_ICON, int2roman(turret.level), turret.userString)]

    def _armor(self, hit):
        # ([material], penetration info) where the chosen hit's line meets the hangar vehicle, None without it.
        chosenShot = self._hitLines.chosenShot
        if chosenShot is None or not self.__hangarSpace.isModelLoaded:
            return None
        entity = self.__hangarSpace.getVehicleEntity()
        if entity is None:
            return None
        position, direction = chosenShot
        return _materials(entity, position - direction * _RAY, position + direction * _RAY,
                          self._overlayPanel.shellParams)

    def _check(self, battle, side, hit, gunShot, armor, waits):
        # The log of what the panel shows the hit with: the hit and its shell once per hit, the hangar vehicle and
        # the armor each time; then the numbers of the hit that do not fit them.
        number = self._hitsPanel.selectedNumber
        key = (battle.battleId, side, number)
        if key != self._checked:
            self._checked = key
            _logger.info('check: hit #%s %s of battle %s: %s', number, side, battle.battleId, hitText(hit))
            _logger.info('check: battle vehicle %s, descr %s', battle.vehicleId, 'yes' if battle.vehicleDescr else 'no')
            if gunShot is not None:
                gun, shot = gunShot
                _logger.info('check: shell %s (%s%s) of gun %s: damage %s, penetration %s, speed %s',
                             shot.shell.name, shot.shell.kind, ' gold' if shot.shell.isGold else '', gun.name,
                             shot.shell.armorDamage, shot.piercingPower, shot.speed)
            else:
                _logger.info('check: no shell of the hit')
        mismatches = []
        wanted = hitsVehicle(battle, side, hit)
        entity = self.__hangarSpace.getVehicleEntity() if self.__hangarSpace.isModelLoaded else None
        shown = modulesText(getattr(entity, 'typeDescriptor', None))
        if isinstance(wanted, tuple):
            wantedText = modulesText(_descriptor(wanted[0], wanted[1].encode('hex') if wanted[1] else ''))
        else:
            wantedText = str(wanted)
        _logger.info('check: hangar vehicle %s, the hit is on %s', shown, wantedText)
        chosenShot = self._hitLines.chosenShot
        # While the hangar changes the vehicle, no line is drawn.
        if chosenShot is not None and shown != wantedText:
            mismatches.append('the hangar vehicle %s is not the hit vehicle %s' % (shown, wantedText))
        if chosenShot is not None:
            position, direction = chosenShot
            _logger.info('check: hit line at (%.3f, %.3f, %.3f), direction (%.3f, %.3f, %.3f)', position.x,
                         position.y, position.z, direction.x, direction.y, direction.z)
        elif hit.points:
            _logger.info('check: no hit line drawn yet for %d points', len(hit.points))
        if armor is not None:
            materials, info = armor
            _logger.info('check: armor: chance %s, result %s; layers %s', getattr(info, 'chance', None),
                         getattr(info, 'resultType', None), ['%s nominal %s resulting %.1f angle %.1f%s' % (
                             material.partName, material.nominalArmor, material.resArmor, material.viewAngle,
                             ' spaced' if material.isSpacedArmor else '') for material in materials])
        elif chosenShot is not None and not waits:
            mismatches.append('the hit line meets no armor of the hangar vehicle')
        isHighExplosive = hit.shellType == 'HIGH_EXPLOSIVE'
        pierced = any(effect in _PIERCED_EFFECTS for effect in hit.hitEffects)
        ricochet = any(effect in _RICOCHET_EFFECTS for effect in hit.hitEffects)
        chance = getattr(armor[1], 'chance', None) if armor is not None else None
        if chance is not None and not isHighExplosive and not hit.isSplash:
            if pierced and chance <= 0:
                mismatches.append('pierced, the garage chance is %s%%' % chance)
            if hit.hitEffects and not pierced and not ricochet and chance >= 100:
                mismatches.append('not pierced, the garage chance is %s%%' % chance)
        if gunShot is not None:
            shell = gunShot[1].shell
            average = shell.armorDamage[0]
            if hit.damage > 0 and pierced and not isHighExplosive and not (
                    (1 - _DAMAGE_SPREAD) * average - 1 <= hit.damage <= (1 + _DAMAGE_SPREAD) * average + 1):
                mismatches.append('damage %s is not the shell average %s +-%d%% (the last hit points, another shell?)'
                                  % (hit.damage, average, _DAMAGE_SPREAD * 100))
            if bool(shell.isGold) != bool(hit.isGoldShell):
                mismatches.append('the shell %s is not of the hit premium flag %s' % (shell.name, hit.isGoldShell))
        for mismatch in mismatches:
            _logger.warning('check: MISMATCH hit #%s %s: %s', number, side, mismatch)

    def _sections(self, hit, gunShot, armor):
        texts = self._texts
        shell = gunShot[1].shell if gunShot is not None else None
        isHighExplosive = hit.shellType == 'HIGH_EXPLOSIVE'
        sections = []
        rows = [(str(int(shell.armorDamage[0])), texts['avgDamage'], False)] if shell is not None else []
        sections.append(self._section('damage', texts['damage'], texts['hp'], str(hit.damage), False, rows))
        if gunShot is not None:
            piercing = gunShot[1].piercingPower
            average = str(int(round(piercing[0])))
            rows = []
            if armor is not None and armor[1] is not None:
                rows.append(('%s%%' % armor[1].chance, texts['chance'], True))
            if hit.distance and not isHighExplosive:
                value = str(int(round(computePiercingPowerAtDist(piercing, hit.distance))))
                rows.insert(0, (average, texts['avgPenetration'], False))
                sections.append(self._section('penetration', texts['penetration'], texts['mm'], value, True, rows))
            else:
                sections.append(self._section('penetration', texts['penetration'], texts['mm'], average, False, rows))
        materials = armor[0] if armor is not None else []
        main = [material for material in materials if not material.isSpacedArmor]
        spaced = [material for material in materials if material.isSpacedArmor]
        if main:
            rows = [(str(int(main[0].nominalArmor)), texts['nominal'], True)]
            if spaced:
                rows.append(('+ %d' % sum(int(material.nominalArmor) for material in spaced), texts['spaced'], True))
            sections.append(self._section('armor', texts['armor'], texts['mm'], str(int(round(main[0].resArmor))),
                                          True, rows))
        else:
            sections.append(self._section('armor', texts['armor'], texts['mm'], _NONE, False, []))
        if not isHighExplosive:
            angle = u'%d°' % int(round(main[0].viewAngle)) if main else _NONE
            rows = []
            if shell is not None:
                from gui.shared.utils.functions import getShellImpactParams
                ricochetCos = getShellImpactParams(shell.type)[0]
                if ricochetCos > 0.0:
                    rows.append((u'> %d°' % int(round(math.degrees(math.acos(ricochetCos)))), texts['ricochet'],
                                 False))
            sections.append(self._section('angle', texts['angle'], '', angle, bool(main), rows))
        distance = str(int(round(hit.distance))) if hit.distance else _NONE
        sections.append(self._section('distance', texts['distance'], texts['m'], distance, False, []))
        rows = []
        for device in hit.damagedDevices:
            name = device.extra[:-len(_HEALTH_SUFFIX)] if device.extra.endswith(_HEALTH_SUFFIX) else device.extra
            rows.append((name or device.device, _DEVICE_STATES.get(device.code, device.code), False))
        sections.append(self._section('crits', texts['crits'], '', str(hit.critsCount), False, rows))
        return sections

    @staticmethod
    def _section(kind, title, units, value, counted, rows):
        section = ShotSectionModel()
        section.setKind(kind)
        section.setTitle(title)
        section.setUnits(units)
        section.setValue(value)
        section.setCounted(counted)
        array = section.getRows()
        for rowValue, label, rowCounted in rows:
            row = ShotRowModel()
            row.setValue(rowValue)
            row.setLabel(label)
            row.setCounted(rowCounted)
            array.addViewModel(row)
        array.invalidate()
        return section
