# Architecture

## Repository

```
build.py                      build the .wotmod, optionally install it
src/gui/mods/                 Python sources, packed to res/scripts/client/gui/mods/ as .pyc
  mod_sagtary_armor_hits.py   entry point: the game imports it and calls init() / fini()
  sagtary_armor_hits/         code of the mod
resources/                    packed to res/ as they are
  gui/gen_resources/            declarations of the mod's own R.mods.sagtary_armor_hits.* resources
  gui/gameface/mods/sagtary_armor_hits/   Gameface pages, scripts and styles
  gui/maps/sagtary_armor_hits/  images
docs/                         notes
```

The game loads every `gui/mods/mod_*.pyc` and then calls its `init()`; `fini()` runs when the client shuts down.
The entry module only wires the parts together; the code is in the package.

Everything in `res/` is shared by the game and all mods, so this mod keeps its files in folders of its own:
`gui/mods/sagtary_armor_hits/`, `gui/maps/sagtary_armor_hits/`, `gui/gameface/mods/sagtary_armor_hits/`. The
declaration file is `gui/gen_resources/sagtary_armor_hits.json`: a file with the name of a client one replaces it.

## Package `sagtary_armor_hits`

Now. The parts depend one way: the entry module wires them; `views/` uses `data/`; `data/` knows nothing of the UI.
The objects are made in the entry module and given to the parts that use them (a `BattleStore` to `HitsScreen`,
which gives it to the window with the keyword arguments of `App.loadView`), so there is no shared state in modules.

Core:

| Module             | Does                                                                         |
|--------------------|------------------------------------------------------------------------------|
| `config.py`        | ids, resource paths, texts, limits                                           |
| `lang.py`          | texts in the client language                                                 |
| `settings.py`      | user settings from `mods/configs/sagtary_armor_hits/config.json`             |
| `optional_mods.py` | the optional third-party mods, or `None` when not installed: OpenWG Gameface (`gfModInject`), ModsList API (`modsListApi`) |

Data, without UI (`data/`):

| Module                    | Does                                                                         |
|---------------------------|------------------------------------------------------------------------------|
| `data/battles.py`         | battles of the session in memory: `Battle` (fields with defaults in `FIELDS`), `BattleStore` (newest first, up to `BATTLES_LIMIT`, `onChanged`), `BattleCollector` (adds the battle on `onAvatarReady`, battles and replays) |
| `data/battle_recorder.py` | raw record of every server call about shots and damage, a JSON Lines file per battle in `mods/sagtary_armor_hits/battles/` |

UI (`views/`), a package per screen or button. The view models, the data the Gameface pages read, are apart in
`views/models/`, like the client's `gui/impl/gen/view_models`; they hold no logic, the views and presenters fill them.

| Module                                    | Does                                                         |
|-------------------------------------------|--------------------------------------------------------------|
| `views/hits/hits_screen.py`               | puts the hits screen into the client: the view setting, the lobby state and its transition; loads the view with the `BattleStore` |
| `views/hits/hits_state.py`                | lobby state of the screen: a page of the lobby navigation, the armor page scene and camera |
| `views/hits/hits_view.py`                 | window and Gameface view of the screen: the full screen page, the mouse over the scene, the panel presenters |
| `views/hits/battle_selector.py`           | presenter of the battle selector: fills its model from the `BattleStore`, keeps the selected battle (`onBattleSelected`) |
| `views/lobby_button/lobby_button.py`      | the hangar button that opens the screen; picks one of the two below |
| `views/lobby_button/mods_list_entry.py`   | entry in the ModsList API mods list (optional)               |
| `views/lobby_button/footer_button.py`     | button of its own in the hangar footer, next to the game menu button |
| `views/models/hits_view_model.py`         | view model of the hits screen                                |
| `views/models/battle_selector_model.py`   | view models of the battle selector and of a battle in its list |
| `views/models/footer_button_model.py`     | view model of the footer button                              |

Planned, as the features come (after Poliroid's Battle Hits, which does the same job):

| Part              | Will do                                                                     |
|-------------------|-----------------------------------------------------------------------------|
| storage           | keep the hits of the last battles between sessions                          |
| hangar scene      | show the vehicle in the hangar with the hit points on its armor             |
| viewer screen     | hits of the selected battle on the hits screen                              |

## Lobby button

ModsList API is optional; the footer button is the main one.

| Installed                                         | Button                              |
|---------------------------------------------------|-------------------------------------|
| OpenWG Gameface                                   | button in the hangar footer         |
| OpenWG Gameface, ModsList API, `useModsList` on   | entry in the ModsList API mods list |
| OpenWG Gameface, ModsList API, `useModsList` off  | button in the hangar footer         |
| neither                                           | no button, a warning in `game.log`  |

ModsList API needs OpenWG Gameface itself, so there is no case with ModsList API alone. `useModsList` is in the
user settings file (see README).

The footer button uses the client's own API where there is one:

- Since client 2.4.1 the client reads `gui/gen_resources/*.json` of all packages into the `R` tree, so the layout
  is `R.mods.sagtary_armor_hits.views.FooterButton`.
- The view is a `ViewComponent`, added as a child view of the footer in `LobbyFooter._initChildren` (and of the
  footers of the modes: Comp7, Comp7 Light, Last Stand, Battle Royale).

The client has no API to put an element into the footer page: the footer script draws only its own children, by
name. So `FooterButton.js` is loaded into the footer page by OpenWG Gameface (`gf_mod_inject`: it replaces the
client's `gui/gameface/js/index.js`, which every Gameface page loads). The script puts the button before the menu
button and calls the view model's `onClick` command. ModsList API and Aslain's Mod Menu add their buttons the same
way.

## Hits screen

The screen is built like the client's vehicle armor page (Vehicle Hub, `VehicleHubWindow`):

- a Scaleform view setting (`ViewSettings`, alias `sagtaryArmorHitsView`, layer `SUB_VIEW`) whose class is a Gameface
  window (`WindowImpl`); it is added to `IGuiLoader.entitiesFactory` when the lobby app initializes;
- the window's content is a Gameface view (`ViewComponent`) with the layout `R.mods.sagtary_armor_hits.views.HitsView`;
  the page is transparent, so the 3D hangar shows through it;
- a lobby state (`SFViewLobbyState`, child of `SubScopeSubLayerState`) is added to the lobby state machine
  (`AppLifeCycleEvent.INITIALIZING`, `addStateConfigurator`); entering it fires a `LOAD_VIEW` event for the alias, and
  the mod loads the view (`app.loadView`), as the client's package business handlers do;
- the lobby draws its header and footer as opaque bars ("old style", CSS class `base__oldStyle` with a background
  pattern) around a sub view in a frame, and the window then gets only the space between them; the Flash lobby page
  (`LobbyPageSubContainer.onViewVisibilityChanged`) leaves a view out of the frame when its wrapper reports
  `isFullScreenModeSupported`, which a Gameface page sets with `viewEnv.setFullscreenModeSupported(true)`;
  `HitsView.js` does that, like the armor page, and puts `viewEnv.getExternalPaddingsRem()` (the space of the header
  and the footer, updated on `self.onPaddingsUpdated`) into the CSS variables `--external-padding-*`;
- the page draws the armor page's shading itself (`Page_base__armor` in `vehicle_hub/main/main.css`) over the whole
  screen, so the dark fade under the footer comes from the page, not from the footer;
- the state has no `LobbyStateFlags.HANGAR` flag: the lobby header picks its type by that flag, and without it shows the
  page header (hangar button, page title, wallet) instead of the full hangar header; the hangar button closes the
  screen;
- the 3D scene is set like on the armor page (the client's `VehicleHubState` and `ArmorState`): entering the state
  moves the hangar vehicle to the customization place (`HangarCustomizationEvent.CHANGE_VEHICLE_MODEL_TRANSFORM`, the
  place and angles of `customizationHangarCFG()`), and leaving it puts the vehicle back
  (`RESET_VEHICLE_MODEL_TRANSFORM`, `turretAndGunAngles.reset()`);
- the state is a `SubhangarStateGroupConfigProvider`: the client's `SubhangarObserver` activates the subhangar groups
  `VehicleHub` and `VehicleHubArmor{Small,Medium,Large}Tank` (by the vehicle size, `selectItemByTankSize`), which
  switches to the armor camera (`Armor_Inspector_Camera`); the camera moves there at once (`CameraMover`), as a smooth
  move would fly it from the hangar up to the customization place;
- the page passes the mouse over the scene to the hangar camera like the client's `SceneWrapper`: a layer under the
  panels sends drags (`dx`, `dy` in pixels) and wheel steps (`dz` of 600) to `onMoveSpace`, which fires
  `CameraRelatedEvents.LOBBY_VIEW_MOUSE_MOVE`, and `onMouseOver3dScene` fires `NOTIFY_CURSOR_OVER_3DSCENE`; the
  panels' container lets the mouse through (`pointer-events: none`), the panels do not.

The battle selector shows the selected battle (map preview `gui/maps/icons/map/small/<map>.png`, map, mode from
`R.strings.menu.loading.battleTypes`, vehicle, date and time in the client format) and opens the list of the session's
battles; it is styled like the client's dropdowns (the armor page's overlay type: the client's arrow and list item
background). The battles are kept in memory only, so the list starts empty with every game start. To add a field:
a field in `Battle.FIELDS` and in `battleFromAvatar`, a property in `BattleItemModel`, a line in `_fillItem`, and its
place on the page.

The armor overlay of the client's armor screen is a CGF component (`ArmorInspectorComponent`) put on the hangar
vehicle, so the hits screen can show it without the Vehicle Hub.

## Logging

All modules log to the `sagtary.armor_hits` logger. The lines go to `game.log` in the game folder, for example
`[INFO] [Main] [SCRIPT] [sagtary.armor_hits] init v0.1.0`.
