# -*- coding: utf-8 -*-
"""Optional third-party mods the mod uses when they are installed: OpenWG Gameface and ModsList API."""


def gfModInject():
    # openwg_gameface.gf_mod_inject, or None when OpenWG Gameface is not installed.
    try:
        from openwg_gameface import gf_mod_inject
    except ImportError:
        return None
    return gf_mod_inject


def modsListApi():
    # The ModsList API, or None when that mod is not installed.
    try:
        from gui.modsListApi import g_modsListApi
    except ImportError:
        return None
    return g_modsListApi
