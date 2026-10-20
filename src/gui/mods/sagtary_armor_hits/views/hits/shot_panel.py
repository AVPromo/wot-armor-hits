# -*- coding: utf-8 -*-
"""Shot panel of the hits screen, on the right: the chosen hit's shooter and target, its result and its numbers.

ShotPanelPresenter fills the view model (views/models/shot_panel_model.py) for the hit the hits panel has chosen:

- the cards of the shooter and the target: the player, the vehicle (the client's name, tier, icon and nation flag)
  with its modules of the battle (the compact descriptor); beside the shooter its gun and the shell of the hit,
  beside the target its turret when it has one (not a turretless vehicle) and its gun, as icons like the armor page's. On the
  received side the shooter is the other vehicle and the target the player's, on the dealt side the other way round.
  Over an icon the client's tooltip of the module (CONTEXT_VEHICLE_MODULE) or of the shell (ARMOR_INSPECTOR_SHELL)
  shows, for the vehicle as the hangar shows it (a maps training copy as the vehicle it copies): tooltipData;
- the sections, each with its icon (the client's damage log icons for damage and modules, the mod's for the others):
  damage (the hit's, the shell's average), penetration (the shell's, at the hit's distance when it is
  known), armor and impact angle (the vehicle's armor where the hit line meets it, counted in the garage like the
  client's armor tooltip does: getMaterialsAtCursor along the line, the shell's penetration chance there,
  calculatePenetrationInfo), distance (recorded in battle) and modules and crew (the damaged ones of the player's
  vehicle, as English text: the extra without 'Health', what the damage info code tells).

The shell is the overlay panel's (overlay_panel.py: the shooter's gun and shot with the hit's shell kind); the hit
line is the hit lines presenter's (hit_lines.py: its first point and direction when drawn). The armor needs the
vehicle's collision model, which comes a few frames after the vehicle: without it the armor is counted again after
_RETRY seconds, up to _TRIES times. The panel is filled once in the frame after a change, as one change comes from
the hits panel and the hit lines together. The armor is what the line meets from _RAY / 2 before the hit point: a
part in front of it is not what the shell hit. A value counted in the garage is marked (counted) for the page.

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
from gui.impl.backport import createTooltipData
from gui.impl.gen import R
from gui.Scaleform.genConsts.TOOLTIPS_CONSTANTS import TOOLTIPS_CONSTANTS
from gui.shared.gui_items.Vehicle import Vehicle
from items import parseIntCompactDescr, vehicles
from items.components.component_constants import MODERN_HE_PIERCING_POWER_REDUCTION_FACTOR_FOR_SHIELDS
from skeletons.gui.shared.utils import IHangarSpace

from gui.mods.sagtary_armor_hits.data.client_names import (clientText, copiedName, shownVehicleDescr,
                                                           shownVehicleId, vehicleShortName)
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
_SHELL_ICON = 'img://gui/maps/icons/shell/x64x64/%s.png'
# The card roles, as the page names them in a tooltip's arguments.
_SHOOTER = 'shooter'
_TARGET = 'target'
_NONE = u'—'
# The shell kind's abbreviation of the client's damage log (AP, APCR, HE, ...), as the hits panel shows it.
_SHELL_TEXT_KEY = '#ingame_gui:damageLog/shellType/%s'
# The armor tooltip's name of an armor layer's part, by VehicleArmorTags.
_PART_TEXT_KEY = '#armor_inspector:tooltip/armor/part/%s'
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


def _shownVehicle(vehicleId, descr):
    # The client's vehicle item as the hangar shows the vehicle, with its modules of the battle; None.
    try:
        strCD = shownVehicleDescr(vehicleId, descr)
        if strCD:
            return Vehicle(strCompactDescr=strCD)
        return Vehicle(typeCompDescr=shownVehicleId(vehicleId) or vehicleId)
    except Exception:
        _logger.debug('shot panel: no vehicle item of %s', vehicleId, exc_info=True)
        return None


def _shownGun(descriptor, gun):
    # The gun of the shown vehicle that the gun is (a maps training gun copies one by name); the installed one.
    for turret in descriptor.type.turrets[0]:
        for item in turret.guns:
            if item.name == copiedName(gun.name):
                return item
    return descriptor.gun


def _hasTurret(descriptor):
    # Not a turretless vehicle: the armor page's test of its turret choice.
    try:
        return len(descriptor.hull.fakeTurrets['lobby']) != len(descriptor.turrets)
    except Exception:
        return True


def _materials(entity, start, end, shellParams):
    # ([material], penetration info) of the vehicle's armor along the segment, like the client's armor tooltip; None
    # when the collision model does not meet the segment (not loaded yet).
    from helpers.collisions import SegmentCollisionResultExt
    from shared_utils.vehicle_utils import getMatinfo
    from gui.impl.lobby.vehicle_hub.sub_presenters.armor.utils import getMaterialsAtCursor, stackMaterials
    from gui.impl.lobby.vehicle_hub.sub_presenters.armor.penetration_utils import calculatePenetrationInfo
    collisions = getattr(entity.appearance, 'collisions', None)
    if collisions is None:
        _logger.info('check: armor: no collision model yet')
        return None
    found = collisions.collideAllWorld(start, end)
    _logger.info('check: armor: collisions along the line (distance, cos, material, part) %s; the hit point is at '
                 '%.2f', [(round(item[0], 3), round(item[1], 3), item[2], item[3]) for item in found or ()], _RAY)
    # What the line meets well before the hit point (another part in front of it: a gun, a track guard) is not what
    # the shell hit there.
    found = [item for item in found or () if item[0] >= _RAY * 0.5]
    if not found or found[0][0] - _RAY > _RAY * 0.5:
        _logger.info('check: armor: the line MISSES the armor at the hit point (model not ready, other modules or '
                     'another vehicle?)')
        return None
    isWheeled = entity.typeDescriptor.type.isWheeledVehicle
    segments = [SegmentCollisionResultExt(distance, angleCos, getMatinfo(entity, part, kind, isWheeled), part)
                for distance, angleCos, kind, part in found]
    # The layers as the client's armor tooltip shows them: the same part's layers stacked (a track twice, x2).
    materials = stackMaterials(getMaterialsAtCursor(entity, segments, shellParams), entity.typeDescriptor.level)
    return materials, calculatePenetrationInfo(shellParams, segments)


class ShotPanelPresenter(object):
    __hangarSpace = dependency.descriptor(IHangarSpace)

    def __init__(self, model, hitsPanel, overlayPanel, hitLines, texts):
        # texts: the section titles and line labels in the client language (config TEXTS 'shot/*').
        self._model = model
        self._hitsPanel = hitsPanel
        self._overlayPanel = overlayPanel
        self._hitLines = hitLines
        self._texts = texts
        # The fill of the next frame or the next try of the armor.
        self._callbackID = None
        self._tries = 0
        # The reasons of the fill to come, for the log.
        self._reasons = []
        # (battle id, side, number) of the hit last logged in full.
        self._checked = None
        # {role: (vehicle item, [(tooltip alias, compact descriptor)] of its modules in order)}
        self._tooltips = {}

    def tooltipData(self, role, index):
        # The client's tooltip of a module of a card, None when there is none.
        vehicle, modules = self._tooltips.get(role, (None, []))
        if vehicle is None or not 0 <= index < len(modules):
            return None
        alias, compactDescr = modules[index]
        calls('shot panel: tooltip', '%s %d: %s %s' % (role, index, alias, compactDescr))
        return createTooltipData(isSpecial=True, specialAlias=alias, specialArgs=(compactDescr, vehicle))

    def init(self):
        with self._model.transaction() as model:
            model.setTooltipContentId(R.views.common.tooltip_window.backport_tooltip_content.BackportTooltipContent())
            model.setTooltipDecoratorId(R.views.common.tooltip_window.tooltip_window.TooltipWindow())
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
        self._tooltips = {}

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
        # One change of the hits panel tells it up to three times (the lines cleared, drawn, the panel changed), and
        # the overlay panel sets the hit's shell after the hit lines: filled once, in the next frame, when all of
        # them are done.
        self._cancel()
        self._tries = 0
        self._reasons.append(reason)
        self._callbackID = BigWorld.callback(0.0, self._onFrame)

    def _onFrame(self):
        self._callbackID = None
        reasons, self._reasons = self._reasons, []
        self._fill(', '.join(reasons))

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
        shooterModules = self._shooterModules(shooter, gunShot)
        targetModules = self._targetModules(target)
        with self._model.transaction() as model:
            model.setIsVisible(True)
            self._fillVehicle(model.shooter, self._texts['shooter'], shooter, shooterModules)
            self._fillVehicle(model.target, self._texts['target'], target, targetModules)
            model.setShellText(clientText(_SHELL_TEXT_KEY % hit.shellType) or '' if hit.shellType else '')
            # The shell shown on the shooter's card, else the hit's premium flag.
            model.setIsGoldShell(bool(gunShot[1].shell.isGold) if gunShot is not None else bool(hit.isGoldShell))
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
        for moduleIcon, moduleTier in modules:
            item = ShotModuleModel()
            item.setIcon(moduleIcon)
            item.setTier(moduleTier)
            array.addViewModel(item)
        array.invalidate()

    def _shooterModules(self, shooter, gunShot):
        # [(icon, tier)] of the shooter's gun and the hit's shell; their tooltips for the shown vehicle.
        self._tooltips[_SHOOTER] = (None, [])
        if gunShot is None:
            return []
        gun, shot = gunShot
        vehicle = _shownVehicle(*shooter[:2])
        if vehicle is not None:
            shownGun = _shownGun(vehicle.descriptor, gun)
            shots = [item for item in shownGun.shots if item.shell.name == copiedName(shot.shell.name)] or [
                item for item in shownGun.shots if item.shell.kind == shot.shell.kind]
            self._tooltips[_SHOOTER] = (vehicle, [
                (TOOLTIPS_CONSTANTS.CONTEXT_VEHICLE_MODULE, shownGun.compactDescr),
                (TOOLTIPS_CONSTANTS.ARMOR_INSPECTOR_SHELL, (shots[0] if shots else shot).shell.compactDescr)])
        return [(_GUN_ICON, int2roman(gun.level)), (_SHELL_ICON % shot.shell.iconName, '')]

    def _targetModules(self, target):
        # [(icon, tier)] of the target's turret (when it has one) and gun, like the armor page's modules; their
        # tooltips for the shown vehicle.
        self._tooltips[_TARGET] = (None, [])
        vehicle = _shownVehicle(*target[:2])
        if vehicle is None:
            return []
        descriptor = vehicle.descriptor
        modules = [descriptor.turret] if _hasTurret(descriptor) else []
        modules.append(descriptor.gun)
        self._tooltips[_TARGET] = (vehicle, [(TOOLTIPS_CONSTANTS.CONTEXT_VEHICLE_MODULE, module.compactDescr)
                                             for module in modules])
        return [(_TURRET_ICON if module is descriptor.turret else _GUN_ICON, int2roman(module.level))
                for module in modules]

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
            if pierced and hit.damage > 0 and chance <= 0:
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
            # A hit without damage events does not know its premium flag: a mismatch only when the gun has another
            # shell of the kind to choose.
            kinds = [shot for shot in gunShot[0].shots if shot.shell.kind == hit.shellType]
            if len(kinds) > 1 and bool(shell.isGold) != bool(hit.isGoldShell):
                mismatches.append('the shell %s is not of the hit premium flag %s' % (shell.name, hit.isGoldShell))
        for mismatch in mismatches:
            _logger.warning('check: MISMATCH hit #%s %s: %s', number, side, mismatch)

    def _sections(self, hit, gunShot, armor):
        texts = self._texts
        shell = gunShot[1].shell if gunShot is not None else None
        isHighExplosive = hit.shellType == 'HIGH_EXPLOSIVE'
        sections = []
        rows = [(str(int(shell.armorDamage[0])), texts['avgDamage'], False)] if shell is not None else []
        if shell is not None and hit.damage > 0 and shell.armorDamage[0] > 0:
            # How far the damage is from the shell's average, in percent of it.
            deviation = int(round((hit.damage - shell.armorDamage[0]) * 100.0 / shell.armorDamage[0]))
            rows.append((u'-%d%%' % -deviation if deviation < 0 else u'+%d%%' % deviation if deviation else u'0%',
                         texts['deviation'], True))
        sections.append(self._section('damage', texts['damage'], str(hit.damage), False, rows))
        if gunShot is not None:
            piercing = gunShot[1].piercingPower
            average = str(int(round(piercing[0])))
            rows = []
            if armor is not None and armor[1] is not None:
                rows.append(('%s%%' % armor[1].chance, texts['chance'], True))
            if hit.distance and not isHighExplosive:
                atDistance = computePiercingPowerAtDist(piercing, hit.distance)
                value = str(int(round(atDistance)))
                rows.insert(0, (average, texts['avgPenetration'], False))
                # What the distance took off the shell's penetration (the shell's average less the value).
                loss = int(round(atDistance)) - int(round(piercing[0]))
                rows.insert(1, (u'-%d' % -loss if loss < 0 else u'%d' % loss,
                                texts['distanceLoss'] % {'distance': int(round(hit.distance))}, True))
                sections.append(self._section('penetration', texts['penetration'], value, True, rows))
            else:
                sections.append(self._section('penetration', texts['penetration'], average, False, rows))
        # The armor as the client's armor tooltip counts it: all the layers on the way, each by its reduction factor
        # (a modern high explosive shell's on spaced armor): the resulting armor; the nominal one with its layers in
        # brackets ('55 nominal (25 Chassis + 30 Hull)'), and the armor the angles add.
        layers = armor[0] if armor is not None else []
        shellParams = self._overlayPanel.shellParams
        reduction = lambda layer: (MODERN_HE_PIERCING_POWER_REDUCTION_FACTOR_FOR_SHIELDS if layer.isSpacedArmor and
                                   getattr(shellParams, 'useHEShell', False) else 1)
        nominal = sum(round(layer.nominalArmor) * reduction(layer) for layer in layers)
        effective = int(round(sum(layer.resArmor * reduction(layer) for layer in layers)))
        if len(layers) > 1:
            parts = u' + '.join(u'%d %s' % (int(round(layer.nominalArmor)), self._layerText(layer)) for layer in layers)
        elif layers:
            parts = self._layerText(layers[0])
        if layers:
            sections.append(self._section('armor', texts['armor'], str(effective), True, [
                (str(int(nominal)), u'%s (%s)' % (texts['nominal'], parts), True),
                (u'+%d' % int(effective - nominal), texts['angleArmor'], True)]))
        else:
            sections.append(self._section('armor', texts['armor'], _NONE, False, []))
        # The angle of the first layer, like the tooltip, for every shell (a high explosive one does not ricochet, but
        # the angle makes its armor thicker too); the ricochet angle only beside it.
        angle = u'%d°' % int(round(layers[0].viewAngle)) if layers else _NONE
        rows = []
        if layers and shell is not None and not isHighExplosive:
            from gui.shared.utils.functions import getShellImpactParams
            ricochetCos = getShellImpactParams(shell.type)[0]
            if ricochetCos > 0.0:
                rows.append((u'> %d°' % int(round(math.degrees(math.acos(ricochetCos)))), texts['ricochet'], False))
        sections.append(self._section('angle', texts['angle'], angle, bool(layers), rows))
        distance = str(int(round(hit.distance))) if hit.distance else _NONE
        sections.append(self._section('distance', texts['distance'], distance, False, []))
        rows = []
        for device in hit.damagedDevices:
            name = device.extra[:-len(_HEALTH_SUFFIX)] if device.extra.endswith(_HEALTH_SUFFIX) else device.extra
            rows.append((name or device.device, _DEVICE_STATES.get(device.code, device.code), False))
        sections.append(self._section('crits', texts['crits'], str(hit.critsCount), False, rows))
        return sections

    @staticmethod
    def _layerText(layer):
        # The layer's part in the client's words, and how many layers of it: 'Chassis x2'.
        name = getattr(layer.partName, 'value', layer.partName)
        text = clientText(_PART_TEXT_KEY % name) or name
        count = getattr(layer, 'count', 1) or 1
        return u'%s x%d' % (text, count) if count > 1 else text

    @staticmethod
    def _section(kind, title, value, counted, rows):
        section = ShotSectionModel()
        section.setKind(kind)
        section.setTitle(title)
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
