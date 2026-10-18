# -*- coding: utf-8 -*-
"""Developer tools of the hits screen: Import reads the battles file into the BattleStore, Export writes the store's
battles to it. The result is shown as a system message of the client (the notifications at the bottom right).
The tools are for the developer only, so their texts are in English.
"""
import logging

from gui import SystemMessages

from gui.mods.sagtary_armor_hits.data.battle_file import BattleFileError

_logger = logging.getLogger('sagtary.armor_hits')

_IMPORT_LABEL = 'Import'
_EXPORT_LABEL = 'Export'
_IMPORTED = u'Armor Hits: %d battles imported from %s'
_EXPORTED = u'Armor Hits: %d battles exported to %s'
_FAILED = u'Armor Hits: %s'


class DevToolsPresenter(object):

    def __init__(self, model, store, battleFile):
        self._model = model
        self._store = store
        self._battleFile = battleFile

    def init(self):
        with self._model.transaction() as model:
            model.setIsVisible(True)
            model.setImportLabel(_IMPORT_LABEL)
            model.setExportLabel(_EXPORT_LABEL)
        self._model.onImport += self._onImport
        self._model.onExport += self._onExport

    def fini(self):
        self._model.onExport -= self._onExport
        self._model.onImport -= self._onImport
        self._model = None
        self._store = None
        self._battleFile = None

    def _onImport(self, *args):
        try:
            battles = self._battleFile.load()
        except BattleFileError as error:
            self._fail(error)
            return
        self._store.addAll(battles)
        self._notify(_IMPORTED % (len(battles), self._battleFile.path), SystemMessages.SM_TYPE.Information)

    def _onExport(self, *args):
        battles = self._store.getBattles()
        try:
            self._battleFile.save(battles)
        except BattleFileError as error:
            self._fail(error)
            return
        self._notify(_EXPORTED % (len(battles), self._battleFile.path), SystemMessages.SM_TYPE.Information)

    def _fail(self, error):
        # The error of the system may be in the system's code page: decoded so that it never breaks the message.
        message = error.args[0] if error.args else ''
        if isinstance(message, str):
            message = message.decode('utf-8', 'replace')
        _logger.warning('dev tools: %s', message)
        self._notify(_FAILED % message, SystemMessages.SM_TYPE.Error)

    @staticmethod
    def _notify(message, messageType):
        SystemMessages.pushMessage(message, type=messageType)
