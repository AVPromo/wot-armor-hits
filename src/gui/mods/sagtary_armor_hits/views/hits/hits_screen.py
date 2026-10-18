# -*- coding: utf-8 -*-
"""The mod's own hits screen over the 3D hangar, built like the client's vehicle armor page (Vehicle Hub).

HitsScreen puts the screen into the client when the lobby app initializes: the Scaleform view setting of the window
(hits_view.HitsWindow) and the lobby state (hits_state.HitsState) with its navigation transition. The state asks for
its view with a LOAD_VIEW event, and HitsScreen loads the view with the data the screen shows (the BattleStore,
and the BattleFile of the developer tools or None).
"""
import logging

from frameworks.wulf import WindowLayer
from gui.Scaleform.framework import ScopeTemplates, ViewSettings
from gui.app_loader.settings import APP_NAME_SPACE
from gui.shared import EVENT_BUS_SCOPE, events, g_eventBus
from gui.shared.events import ViewEventType
from helpers import dependency
from skeletons.gui.app_loader import IAppLoader
from skeletons.gui.impl import IGuiLoader

from gui.mods.sagtary_armor_hits.views.hits.hits_state import HitsState
from gui.mods.sagtary_armor_hits.views.hits.hits_view import VIEW_ALIAS, HitsWindow

_logger = logging.getLogger('sagtary.armor_hits')


def _registerStates(machine):
    machine.addState(HitsState())


def _registerTransitions(machine):
    machine.addNavigationTransitionFromParent(machine.getStateByCls(HitsState))


class HitsScreen(object):

    def __init__(self, battleStore, battleFile=None):
        self._battleStore = battleStore
        self._battleFile = battleFile

    def install(self):
        g_eventBus.addListener(events.AppLifeCycleEvent.INITIALIZING, self._onAppInitializing)
        g_eventBus.addListener(ViewEventType.LOAD_VIEW, self._onLoadView, EVENT_BUS_SCOPE.LOBBY)

    def uninstall(self):
        g_eventBus.removeListener(events.AppLifeCycleEvent.INITIALIZING, self._onAppInitializing)
        g_eventBus.removeListener(ViewEventType.LOAD_VIEW, self._onLoadView, EVENT_BUS_SCOPE.LOBBY)

    @staticmethod
    def open():
        HitsState.goTo()

    @staticmethod
    def _onAppInitializing(event):
        if event.ns != APP_NAME_SPACE.SF_LOBBY:
            return
        try:
            factory = dependency.instance(IGuiLoader).entitiesFactory
            if factory.getSettings(VIEW_ALIAS) is None:
                factory.addSettings(ViewSettings(VIEW_ALIAS, HitsWindow, '', WindowLayer.SUB_VIEW, VIEW_ALIAS,
                                                 ScopeTemplates.LOBBY_SUB_SCOPE))
            machine = dependency.instance(IAppLoader).getApp().stateMachine
            machine.addStateConfigurator(_registerStates)
            machine.addTransitionConfigurator(_registerTransitions)
        except Exception:
            _logger.exception('hits screen: cannot add the lobby state')

    def _onLoadView(self, event):
        # The lobby state asks for its view with a LOAD_VIEW event; the client's pages are loaded the same way by
        # their package business handlers. The keyword arguments go to HitsWindow.
        if event.alias != VIEW_ALIAS:
            return
        try:
            dependency.instance(IAppLoader).getApp().loadView(event.loadParams, ctx=event.ctx,
                                                               battleStore=self._battleStore,
                                                               battleFile=self._battleFile)
        except Exception:
            _logger.exception('hits screen: cannot load the view')
