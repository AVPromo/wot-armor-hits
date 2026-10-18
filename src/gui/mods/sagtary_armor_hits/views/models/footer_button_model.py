# -*- coding: utf-8 -*-
"""View model of the hangar footer button: its texts, the click, and the inject model of OpenWG Gameface that loads
the button's script and style into the footer page.
"""
from frameworks.wulf import ViewModel

from gui.mods.sagtary_armor_hits.config import FOOTER_BUTTON_MODEL, FOOTER_BUTTON_SCRIPT, FOOTER_BUTTON_STYLE
from gui.mods.sagtary_armor_hits.optional_mods import gfModInject


class FooterButtonModel(ViewModel):

    def __init__(self, properties=3, commands=1):
        # 2 texts and the inject model of OpenWG Gameface.
        super(FooterButtonModel, self).__init__(properties=properties, commands=commands)

    def getTitle(self):
        return self._getString(0)

    def setTitle(self, value):
        self._setString(0, value)

    def getDescription(self):
        return self._getString(1)

    def setDescription(self, value):
        self._setString(1, value)

    def _initialize(self):
        super(FooterButtonModel, self)._initialize()
        self._addStringProperty('title', '')
        self._addStringProperty('description', '')
        self.onClick = self._addCommand('onClick')
        gfModInject()(self, FOOTER_BUTTON_MODEL, styles=[FOOTER_BUTTON_STYLE], modules=[FOOTER_BUTTON_SCRIPT])
