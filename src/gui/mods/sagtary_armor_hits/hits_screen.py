# -*- coding: utf-8 -*-
"""The mod's own hits screen over the 3D hangar.

The screen is a page of the client's lobby navigation, built like the client's vehicle armor page (Vehicle Hub):
- a Scaleform view setting whose class is a Gameface window (WindowImpl) in the sub view layer; the window's content
  is a Gameface view (ViewComponent) with the layout R.mods.sagtary_armor_hits.views.HitsView, declared in
  res/gui/gen_resources/sagtary_armor_hits.json;
- a lobby state (SFViewLobbyState) that loads the view by its alias; the state is added to the lobby state machine
  when the lobby app initializes.

The lobby draws its header and footer as opaque bars ("old style") around a sub view in a frame. A view is out of the
frame when it supports the full screen mode: the page tells it with viewEnv.setFullscreenModeSupported(true) in
HitsView.js, like the client's armor page, and places its content by the external paddings the lobby gives for the
header and the footer.

The state has no LobbyStateFlags.HANGAR flag, so the lobby shows the page header (the hangar button, the page title,
the wallet) and not the full hangar header. The header's hangar button closes the screen.

While the screen is open the hangar shows no vehicle; leaving it puts the current vehicle back.
"""
import logging

from CurrentVehicle import g_currentVehicle
from frameworks.wulf import ViewModel, WindowFlags, WindowLayer
from gui.Scaleform.framework import ScopeTemplates, ViewSettings
from gui.Scaleform.framework.entities.View import ViewKey
from gui.app_loader.settings import APP_NAME_SPACE
from gui.impl.gen import R
from gui.impl.pub import WindowImpl
from gui.impl.pub.view_component import ViewComponent
from gui.lobby_state_machine.states import LobbyStateDescription, SFViewLobbyState, SubScopeSubLayerState
from gui.shared import EVENT_BUS_SCOPE, events, g_eventBus
from gui.shared.events import ViewEventType
from helpers import dependency
from skeletons.gui.app_loader import IAppLoader
from skeletons.gui.impl import IGuiLoader
from skeletons.gui.shared.utils import IHangarSpace

from gui.mods.sagtary_armor_hits.lang import text

_logger = logging.getLogger('sagtary.armor_hits')

_VIEW_ALIAS = 'sagtaryArmorHitsView'


class _HitsView(ViewComponent):

    def __init__(self, *args, **kwargs):
        super(_HitsView, self).__init__(R.mods.sagtary_armor_hits.views.HitsView(), ViewModel, *args, **kwargs)


class _HitsWindow(WindowImpl):

    def __init__(self, layer, **kwargs):
        super(_HitsWindow, self).__init__(content=_HitsView(), wndFlags=WindowFlags.WINDOW, layer=layer)


@SubScopeSubLayerState.parentOf
class _HitsState(SFViewLobbyState):
    STATE_ID = 'sagtaryArmorHits'
    VIEW_KEY = ViewKey(_VIEW_ALIAS)
    __hangarSpace = dependency.descriptor(IHangarSpace)

    def getNavigationDescription(self):
        return LobbyStateDescription(title=text('lobbyButton/name'))

    def _onEntered(self, event):
        super(_HitsState, self)._onEntered(event)
        _logger.info('hits screen: opened')
        try:
            self.__hangarSpace.removeVehicle()
        except Exception:
            _logger.exception('hits screen: cannot remove the hangar vehicle')

    def _onExited(self):
        try:
            g_currentVehicle.refreshModel()
        except Exception:
            _logger.exception('hits screen: cannot restore the hangar vehicle')
        _logger.info('hits screen: closed')
        super(_HitsState, self)._onExited()


def _registerStates(machine):
    machine.addState(_HitsState())


def _registerTransitions(machine):
    machine.addNavigationTransitionFromParent(machine.getStateByCls(_HitsState))


class HitsScreen(object):

    def install(self):
        g_eventBus.addListener(events.AppLifeCycleEvent.INITIALIZING, self._onAppInitializing)
        g_eventBus.addListener(ViewEventType.LOAD_VIEW, self._onLoadView, EVENT_BUS_SCOPE.LOBBY)

    def uninstall(self):
        g_eventBus.removeListener(events.AppLifeCycleEvent.INITIALIZING, self._onAppInitializing)
        g_eventBus.removeListener(ViewEventType.LOAD_VIEW, self._onLoadView, EVENT_BUS_SCOPE.LOBBY)

    def open(self):
        _HitsState.goTo()

    @staticmethod
    def _onAppInitializing(event):
        if event.ns != APP_NAME_SPACE.SF_LOBBY:
            return
        try:
            factory = dependency.instance(IGuiLoader).entitiesFactory
            if factory.getSettings(_VIEW_ALIAS) is None:
                factory.addSettings(ViewSettings(_VIEW_ALIAS, _HitsWindow, '', WindowLayer.SUB_VIEW, _VIEW_ALIAS,
                                                 ScopeTemplates.LOBBY_SUB_SCOPE))
            machine = dependency.instance(IAppLoader).getApp().stateMachine
            machine.addStateConfigurator(_registerStates)
            machine.addTransitionConfigurator(_registerTransitions)
        except Exception:
            _logger.exception('hits screen: cannot add the lobby state')

    @staticmethod
    def _onLoadView(event):
        # The lobby state asks for its view with a LOAD_VIEW event; the client's pages are loaded the same way by
        # their package business handlers.
        if event.alias != _VIEW_ALIAS:
            return
        try:
            dependency.instance(IAppLoader).getApp().loadView(event.loadParams, ctx=event.ctx)
        except Exception:
            _logger.exception('hits screen: cannot load the view')
