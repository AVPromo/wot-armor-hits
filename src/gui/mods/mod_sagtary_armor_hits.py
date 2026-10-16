# -*- coding: utf-8 -*-
"""Armor Hits by Sagtary: hangar viewer of hits received and dealt in battle.

Entry point loaded by the game; the code is in the gui.mods.sagtary_armor_hits package.
"""
import logging

from gui.mods.sagtary_armor_hits import settings
from gui.mods.sagtary_armor_hits.lobby_button import LobbyButton

__version__ = '0.1.0'

_logger = logging.getLogger('sagtary.armor_hits')


def _openViewer():
    # The viewer screen is not there yet.
    _logger.info('lobby button clicked')


_button = LobbyButton(_openViewer)


def init():
    # Called by gui.mods after all mods are imported.
    _button.add(settings.load()['useModsList'])
    _logger.info('init v%s', __version__)


def fini():
    # Called by gui.mods when the client shuts down.
    _button.remove()
