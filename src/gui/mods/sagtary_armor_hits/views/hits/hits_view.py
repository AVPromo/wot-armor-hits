# -*- coding: utf-8 -*-
"""Gameface view and window of the hits screen.

HitsWindow is the class of the Scaleform view setting of the screen: a Gameface window (WindowImpl) in the sub view
layer. Its content, HitsView, is a Gameface view with the layout R.mods.sagtary_armor_hits.views.HitsView, declared in
res/gui/gen_resources/sagtary_armor_hits.json.

The lobby draws its header and footer as opaque bars ("old style") around a sub view in a frame. A view is out of the
frame when it supports the full screen mode: the page tells it with viewEnv.setFullscreenModeSupported(true) in
HitsView.js, like the client's armor page, and places its content by the external paddings the lobby gives for the
header and the footer.

The page passes mouse drags and the wheel over the 3D scene to the hangar camera (onMoveSpace, onMouseOver3dScene),
like the client's SceneWrapper, so the camera turns around the vehicle. The panels and the hangar vehicle have
presenters of their own, made here with the data they show. The developer tools (Import and Export of the battles file) are there only when
the view is given a battle file (config.DEV_TOOLS).
"""
from frameworks.wulf import WindowFlags
from gui.hangar_cameras.hangar_camera_common import CameraRelatedEvents
from gui.impl.gen import R
from gui.impl.pub import WindowImpl
from gui.impl.pub.view_component import ViewComponent
from gui.shared import EVENT_BUS_SCOPE, events, g_eventBus

from gui.mods.sagtary_armor_hits.lang import text
from gui.mods.sagtary_armor_hits.views.hits.battle_selector import BattleSelectorPresenter
from gui.mods.sagtary_armor_hits.views.hits.dev_tools import DevToolsPresenter
from gui.mods.sagtary_armor_hits.views.hits.hangar_vehicle import HangarVehiclePresenter
from gui.mods.sagtary_armor_hits.views.hits.hits_panel import HitsPanelPresenter
from gui.mods.sagtary_armor_hits.views.models.hits_view_model import HitsViewModel

# Alias of the Scaleform view setting of the screen.
VIEW_ALIAS = 'sagtaryArmorHitsView'


class HitsView(ViewComponent):

    def __init__(self, battleStore, battleFile=None):
        super(HitsView, self).__init__(R.mods.sagtary_armor_hits.views.HitsView(), HitsViewModel)
        self._battleStore = battleStore
        self._battleFile = battleFile
        self._presenters = []

    def _getEvents(self):
        model = self.getViewModel()
        return ((model.onMoveSpace, self.__onMoveSpace), (model.onMouseOver3dScene, self.__onMouseOver3dScene))

    def _onLoading(self, *args, **kwargs):
        super(HitsView, self)._onLoading(*args, **kwargs)
        model = self.getViewModel()
        battleSelector = BattleSelectorPresenter(model.battleSelector, self._battleStore, {
            'empty': text('battles/empty')})
        self._presenters.append(battleSelector)
        # The hits panel shows the battle the selector shows, so it is made and set up after the selector.
        hitsPanel = HitsPanelPresenter(model.hitsPanel, self._battleStore, battleSelector, {
            'received': text('hits/received'), 'dealt': text('hits/dealt')})
        self._presenters.append(hitsPanel)
        # The hangar shows the vehicle the hits panel shows the hits on.
        self._presenters.append(HangarVehiclePresenter(hitsPanel))
        if self._battleFile is not None:
            self._presenters.append(DevToolsPresenter(model.devTools, self._battleStore, self._battleFile))
        for presenter in self._presenters:
            presenter.init()

    def _finalize(self):
        for presenter in reversed(self._presenters):
            presenter.fini()
        self._presenters = []
        self._battleStore = None
        self._battleFile = None
        super(HitsView, self)._finalize()

    @staticmethod
    def __onMoveSpace(args=None):
        # Same as the client's Vehicle Hub view: the hangar camera turns and zooms by these deltas.
        if not args:
            return
        g_eventBus.handleEvent(CameraRelatedEvents(CameraRelatedEvents.LOBBY_VIEW_MOUSE_MOVE, ctx={
            'dx': args.get('dx'), 'dy': args.get('dy'), 'dz': args.get('dz')}), EVENT_BUS_SCOPE.GLOBAL)

    @staticmethod
    def __onMouseOver3dScene(args=None):
        isOver = bool(args.get('isOver3dScene')) if args else False
        g_eventBus.handleEvent(events.LobbySimpleEvent(events.LobbySimpleEvent.NOTIFY_CURSOR_OVER_3DSCENE, ctx={
            'isOver3dScene': isOver}))


class HitsWindow(WindowImpl):

    def __init__(self, layer, battleStore, battleFile=None, **kwargs):
        # The client's view loader makes the window with the keyword arguments of App.loadView: HitsScreen gives the
        # battleStore and the battleFile there, the lobby state gives its ctx.
        super(HitsWindow, self).__init__(content=HitsView(battleStore, battleFile), wndFlags=WindowFlags.WINDOW,
                                         layer=layer)
