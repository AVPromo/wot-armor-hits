# -*- coding: utf-8 -*-
"""Armor Hits by Sagtary: hangar viewer of hits received and dealt in battle.

Entry point loaded by the game. For now it only adds a button to the mods list (ModsList API)
that writes a line to game.log when clicked.
"""
import logging

__version__ = '0.1.0'

MODSLIST_ID = 'sagtary_armor_hits'
MODSLIST_ICON = 'gui/maps/sagtary_armor_hits/modslist.png'

_logger = logging.getLogger('sagtary.armor_hits')


def _onButtonClick():
    _logger.info('mods list button clicked')


def _registerButton():
    try:
        from gui.modsListApi import g_modsListApi
    except ImportError:
        _logger.warning('ModsList API not installed, no button')
        return
    g_modsListApi.addModification(
        id=MODSLIST_ID,
        name='Armor Hits',
        description='Hits received and dealt in battle',
        icon=MODSLIST_ICON,
        enabled=True,
        login=False,
        lobby=True,
        callback=_onButtonClick)


_registerButton()
_logger.info('init v%s', __version__)
