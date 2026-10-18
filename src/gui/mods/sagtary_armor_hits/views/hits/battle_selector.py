# -*- coding: utf-8 -*-
"""Battle selector of the hits screen: the selected battle card and the list of the session's battles.

BattleSelectorPresenter fills the view model (views/models/battle_selector_model.py) from the BattleStore, keeps the
selected battle and tells its listeners when the selection changes (onBattleSelected). A new field of a battle is a
property of BattleItemModel and a line in _fillItem. The texts the client has (map, mode, vehicle, date, time) are in
the client language; the battle id goes to the page as a string, as it does not fit a JavaScript number.
"""
import logging

from Event import Event
from gui.impl import backport
from gui.impl.gen import R

from gui.mods.sagtary_armor_hits.views.models.battle_selector_model import BattleItemModel

_logger = logging.getLogger('sagtary.armor_hits')

# Map preview, 100 x 60, by the map folder name.
_MAP_IMAGE = 'img://gui/maps/icons/map/small/%s.png'


def _modeName(battle):
    resource = R.strings.menu.loading.battleTypes.num(battle.arenaGuiType)
    return backport.text(resource()) if resource.exists() else ''


def _fillItem(item, battle):
    item.setId(str(battle.battleID))
    item.setMapName(battle.mapName or battle.geometryName)
    item.setMapImage(_MAP_IMAGE % battle.geometryName if battle.geometryName else '')
    item.setMode(_modeName(battle))
    item.setVehicleName(battle.vehicleName)
    item.setDate(backport.getShortDateFormat(battle.startTime))
    item.setTime(backport.getShortTimeFormat(battle.startTime))


class BattleSelectorPresenter(object):

    def __init__(self, model, store, texts):
        # texts: {'empty': ..., 'list': ...} in the client language.
        self._model = model
        self._store = store
        self._texts = texts
        self._selectedID = None
        self.onBattleSelected = Event()

    @property
    def selectedBattle(self):
        return self._store.getBattle(self._selectedID) if self._selectedID is not None else None

    def init(self):
        with self._model.transaction() as model:
            model.setEmptyTitle(self._texts['empty'])
            model.setListTitle(self._texts['list'])
        self._model.onSelect += self._onSelect
        self._store.onChanged += self._onStoreChanged
        self._update()

    def fini(self):
        self._store.onChanged -= self._onStoreChanged
        self._model.onSelect -= self._onSelect
        self.onBattleSelected.clear()
        self._model = None
        self._store = None

    def select(self, battleID):
        if self._store.getBattle(battleID) is None or battleID == self._selectedID:
            return
        self._selectedID = battleID
        self._model.setSelectedId(str(battleID))
        self.onBattleSelected(self.selectedBattle)

    def _onStoreChanged(self):
        self._update()

    def _update(self):
        battles = self._store.getBattles()
        previous = self._selectedID
        if self._store.getBattle(previous) is None:
            # Nothing selected yet, or the selected battle is gone: the newest one.
            self._selectedID = battles[0].battleID if battles else None
        with self._model.transaction() as model:
            items = model.getBattles()
            items.clear()
            for battle in battles:
                item = BattleItemModel()
                _fillItem(item, battle)
                items.addViewModel(item)
            items.invalidate()
            model.setSelectedId(str(self._selectedID) if self._selectedID is not None else '')
        if self._selectedID != previous:
            self.onBattleSelected(self.selectedBattle)

    def _onSelect(self, args=None):
        battleID = (args or {}).get('id')
        for battle in self._store.getBattles():
            if str(battle.battleID) == battleID:
                _logger.info('battle selector: %s', battle.battleID)
                self.select(battle.battleID)
                return
        _logger.warning('battle selector: unknown battle %r', battleID)
