# -*- coding: utf-8 -*-
"""Armor Hits by Sagtary: hangar viewer of hits received and dealt in battle.

Entry point loaded by the game; the code is in the gui.mods.sagtary_armor_hits package.
"""
import logging

from gui.mods.sagtary_armor_hits import settings
from gui.mods.sagtary_armor_hits.data.battle_recorder import BattleRecorder
from gui.mods.sagtary_armor_hits.data.battles import BattleCollector, BattleStore
from gui.mods.sagtary_armor_hits.views.hits.hits_screen import HitsScreen
from gui.mods.sagtary_armor_hits.views.lobby_button.lobby_button import LobbyButton

__version__ = '0.1.0'

_logger = logging.getLogger('sagtary.armor_hits')


def _openViewer():
    # The mod's own hits screen; only the layout of its panels for now.
    _logger.info('lobby button clicked')
    _hitsScreen.open()


_battleRecorder = BattleRecorder()
_battleStore = BattleStore()
_battleCollector = BattleCollector(_battleStore)
_hitsScreen = HitsScreen(_battleStore)
_button = LobbyButton(_openViewer)


def init():
    # Called by gui.mods after all mods are imported.
    _battleRecorder.install()
    _battleCollector.install()
    _hitsScreen.install()
    _button.add(settings.load()['useModsList'])
    _logger.info('init v%s', __version__)


def fini():
    # Called by gui.mods when the client shuts down.
    _button.remove()
    _battleRecorder.uninstall()
    _battleCollector.uninstall()
    _hitsScreen.uninstall()
