# -*- coding: utf-8 -*-
"""Armor Hits by Sagtary: hangar viewer of hits received and dealt in battle.

Entry point loaded by the game; the code is in the gui.mods.sagtary_armor_hits package.
"""
import logging

from gui.mods.sagtary_armor_hits import settings
from gui.mods.sagtary_armor_hits.config import BATTLE_FILES_DIR
from gui.mods.sagtary_armor_hits.data.battle_file import BattleFiles
from gui.mods.sagtary_armor_hits.data.battles import BattleCollector, BattleStore
from gui.mods.sagtary_armor_hits.data.debug_recorder import DebugRecorder
from gui.mods.sagtary_armor_hits.data.hit_collector import HitCollector
from gui.mods.sagtary_armor_hits.data.hooks import ClientHooks
from gui.mods.sagtary_armor_hits.views.hits.hits_screen import HitsScreen
from gui.mods.sagtary_armor_hits.views.lobby_button.lobby_button import LobbyButton

__version__ = '0.184.0'

_logger = logging.getLogger('sagtary.armor_hits')


def _openViewer():
    # The mod's own hits screen; only the layout of its panels for now.
    _logger.info('lobby button clicked')
    _hitsScreen.open()


# The settings, changed by the hits screen's settings menu too.
_settings = settings.ModSettings()
# The client's methods the debug record and the hit collector listen to, each wrapped once.
_hooks = ClientHooks()
# On only with the "debug" setting.
_debugRecorder = DebugRecorder(_hooks)
_battleStore = BattleStore()
_battleCollector = BattleCollector(_battleStore)
_hitCollector = HitCollector(_battleStore, _hooks)
# The battle files of the hits screen's save and load buttons.
_battleFiles = BattleFiles(BATTLE_FILES_DIR, __version__)
_hitsScreen = HitsScreen(_battleStore, _battleFiles, _settings)
_button = LobbyButton(_openViewer)


def _onSettingChanged(key):
    # The debug record starts and stops with its setting; the lobby button's place changes with the next client start.
    if key == 'debug':
        if _settings.values['debug']:
            _debugRecorder.install()
        else:
            _debugRecorder.uninstall()


def init():
    # Called by gui.mods after all mods are imported.
    values = _settings.load()
    _settings.onChanged += _onSettingChanged
    if values['debug']:
        _debugRecorder.install()
    _battleCollector.install()
    _hitCollector.install()
    _hitsScreen.install()
    _button.add(values['showButtonInModsMenu'])
    _logger.info('init v%s%s', __version__, ', debug record on' if values['debug'] else '')


def fini():
    # Called by gui.mods when the client shuts down.
    _settings.onChanged -= _onSettingChanged
    _button.remove()
    _debugRecorder.uninstall()
    _hitCollector.uninstall()
    _battleCollector.uninstall()
    _hitsScreen.uninstall()
