# -*- coding: utf-8 -*-
"""File buttons of the hits screen: save the chosen battle to its own file, and load the battles of all the battle
files of the folder into the BattleStore. A player sends a battle's file with a report, and the battle is looked at on
another client: the file is put into the folder and loaded. The buttons are an icon and a label each, in the settings
menu under the settings; the save is off while no battle is chosen. The result is the client's toast (a system message: the
popup at the bottom right, then in the notification center) with the full path of the file or the folder.
"""
import logging
import os

from gui import SystemMessages
from gui.shared.notifications import NotificationPriorityLevel

from gui.mods.sagtary_armor_hits.data.battle_file import BattleFileError
from gui.mods.sagtary_armor_hits.trace import calls

_logger = logging.getLogger('sagtary.armor_hits')


def _fullPath(path):
    return os.path.abspath(path).decode('mbcs', 'replace')


class FileButtonsPresenter(object):

    def __init__(self, model, store, battleFiles, hitsPanel, texts):
        # texts: {'save', 'import', 'imported', 'exported', 'failed'} in the client language, with %(count)s, %(path)s,
        # %(error)s.
        self._model = model
        self._store = store
        self._battleFiles = battleFiles
        self._hitsPanel = hitsPanel
        self._texts = texts

    def init(self):
        with self._model.transaction() as model:
            model.setSaveLabel(self._texts['save'])
            model.setImportLabel(self._texts['import'])
        self._model.onSave += self._onSave
        self._model.onImport += self._onImport
        self._hitsPanel.onChanged += self._update
        self._update()

    def fini(self):
        self._hitsPanel.onChanged -= self._update
        self._model.onImport -= self._onImport
        self._model.onSave -= self._onSave
        self._model = None
        self._store = None
        self._battleFiles = None
        self._hitsPanel = None

    def _chosenBattle(self):
        return self._hitsPanel.selection[0]

    def _update(self, *args):
        calls('file buttons: update')
        self._model.setCanSave(self._chosenBattle() is not None)

    def _onImport(self, *args):
        try:
            battles, errors = self._battleFiles.loadAll()
        except BattleFileError as error:
            self._fail([error])
            return
        if battles:
            self._store.addAll(battles)
        text = self._texts['imported'] % {'count': len(battles), 'path': _fullPath(self._battleFiles.folder)}
        if errors:
            self._fail([error for _, error in errors], text)
        else:
            self._toast(text, SystemMessages.SM_TYPE.Information)

    def _onSave(self, *args):
        battle = self._chosenBattle()
        if battle is None:
            return
        try:
            path = self._battleFiles.save(battle)
        except BattleFileError as error:
            self._fail([error])
            return
        self._toast(self._texts['exported'] % {'path': _fullPath(path)}, SystemMessages.SM_TYPE.Information)

    def _fail(self, errors, before=None):
        # The errors of the system may be in the system's code page: decoded so that they never break the toast.
        lines = [before] if before else []
        for error in errors:
            message = error.args[0] if error.args else ''
            if isinstance(message, str):
                message = message.decode('utf-8', 'replace')
            _logger.warning('file buttons: %s', message)
            lines.append(self._texts['failed'] % {'error': message})
        self._toast(u'\n'.join(lines), SystemMessages.SM_TYPE.Error)

    @staticmethod
    def _toast(text, messageType):
        # Medium priority: the popup shows, not only the notification center.
        SystemMessages.pushMessage(text, type=messageType, priority=NotificationPriorityLevel.MEDIUM)
