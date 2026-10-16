# -*- coding: utf-8 -*-
"""Texts in the client language."""
from helpers import getClientLanguage

from gui.mods.sagtary_armor_hits.config import TEXTS


def text(key):
    texts = TEXTS.get(getClientLanguage(), TEXTS['en'])
    return texts.get(key, TEXTS['en'][key])
