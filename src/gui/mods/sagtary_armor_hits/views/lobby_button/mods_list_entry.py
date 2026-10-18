# -*- coding: utf-8 -*-
"""Entry in the hangar mods list of ModsList API (also shown by Aslain's Mod Menu).

ModsList API is an optional third-party mod; without it the lobby button is in the hangar footer.
"""
from gui.mods.sagtary_armor_hits.config import LOBBY_BUTTON_ICON, LOBBY_BUTTON_ID
from gui.mods.sagtary_armor_hits.lang import text


class ModsListEntry(object):

    def __init__(self, api, onClick):
        self._api = api
        self._onClick = onClick

    def add(self):
        self._api.addModification(
            id=LOBBY_BUTTON_ID,
            name=text('lobbyButton/name'),
            description=text('lobbyButton/description'),
            icon=LOBBY_BUTTON_ICON,
            enabled=True,
            login=False,
            lobby=True,
            callback=self._onClick)

    def remove(self):
        self._api.removeModification(LOBBY_BUTTON_ID)
