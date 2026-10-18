# -*- coding: utf-8 -*-
"""Battles saved to a JSON file and read back, to test the hits screen without playing a battle first.

The file:
    {
      "formatVersion": 1,         # version of this layout; a file of a newer layout is not read
      "appVersion": "0.1.0",      # version of the mod that wrote the file
      "exportTime": 1760781180.0, # when it was written, Unix time
      "battles": [{...}, ...]     # Battle fields, newest first
    }
A battle is read with the fields Battle knows: a field the file does not have gets its default, a field Battle does
not know is skipped. So a file written by an older or a newer version of the mod is read as long as the layout is the
same.
"""
import io
import json
import logging
import os
import time
from collections import OrderedDict

from gui.mods.sagtary_armor_hits.data.battles import Battle

_logger = logging.getLogger('sagtary.armor_hits')

FORMAT_VERSION = 1


class BattleFileError(Exception):
    pass


def _text(value):
    # The client gives texts as UTF-8 byte strings or as unicode; json needs one kind to write them as they are.
    if isinstance(value, str):
        return value.decode('utf-8', 'replace')
    if isinstance(value, dict):
        return OrderedDict((key, _text(item)) for key, item in value.items())
    if isinstance(value, list):
        return [_text(item) for item in value]
    return value


def _battleData(battle):
    return _text(battle.toDict())


class BattleFile(object):

    def __init__(self, path, appVersion):
        self._path = path
        self._appVersion = appVersion

    @property
    def path(self):
        return self._path

    def save(self, battles):
        data = OrderedDict((
            ('formatVersion', FORMAT_VERSION),
            ('appVersion', self._appVersion),
            ('exportTime', time.time()),
            ('battles', [_battleData(battle) for battle in battles]),
        ))
        try:
            folder = os.path.dirname(self._path)
            if folder and not os.path.isdir(folder):
                os.makedirs(folder)
            # separators: Python 2 puts a space at the line ends after the commas by default.
            content = json.dumps(data, indent=2, separators=(',', ': '), ensure_ascii=False)
            if isinstance(content, str):
                # Only ASCII texts: json gives a byte string.
                content = content.decode('ascii')
            with io.open(self._path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
        except (IOError, OSError, TypeError, ValueError) as error:
            raise BattleFileError('cannot write %s: %s' % (self._path, error))
        _logger.info('battle file: %d battles written to %s', len(battles), self._path)

    def load(self):
        # The battles of the file, newest first.
        if not os.path.isfile(self._path):
            raise BattleFileError('no file %s' % self._path)
        try:
            with io.open(self._path, encoding='utf-8') as f:
                data = json.load(f)
        except (IOError, OSError, ValueError) as error:
            raise BattleFileError('cannot read %s: %s' % (self._path, error))
        if not isinstance(data, dict) or not isinstance(data.get('battles'), list):
            raise BattleFileError('%s is not a battles file' % self._path)
        formatVersion = data.get('formatVersion')
        if not isinstance(formatVersion, int) or formatVersion > FORMAT_VERSION:
            raise BattleFileError('%s has format version %r, this mod reads up to %d' % (
                self._path, formatVersion, FORMAT_VERSION))
        battles = [Battle.fromDict(item) for item in data['battles'] if isinstance(item, dict)]
        _logger.info('battle file: %d battles read from %s (app version %s)', len(battles), self._path,
                     data.get('appVersion'))
        return battles
