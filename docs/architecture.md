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

Now:

| Module               | Does                                                                 |
|----------------------|----------------------------------------------------------------------|
| `config.py`          | ids, resource paths, texts                                           |
| `lang.py`            | texts in the client language                                         |
| `settings.py`        | user settings from `mods/configs/sagtary_armor_hits/config.json`     |
| `lobby_button.py`    | the hangar button that opens the viewer; picks one of the two below  |
| `mods_list_entry.py` | entry in the ModsList API mods list (optional)                       |
| `footer_button.py`   | button of its own in the hangar footer, next to the game menu button |
| `hits_screen.py`     | the mod's own hits screen over the 3D hangar, a page of the lobby navigation; for now only the layout of its panels, the hangar shows no vehicle while it is open |
| `battle_recorder.py` | raw record of every server call about shots and damage, a JSON Lines file per battle in `mods/sagtary_armor_hits/battles/` |

Planned, as the features come (after Poliroid's Battle Hits, which does the same job):

| Part              | Will do                                                                     |
|-------------------|-----------------------------------------------------------------------------|
| storage           | keep the hits of the last battles between sessions                          |
| hangar scene      | show the vehicle in the hangar with the hit points on its armor             |
| viewer screen     | list of battles and hits on the hits screen                                 |

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
- entering the state removes the vehicle from the hangar (`IHangarSpace.removeVehicle`), leaving it puts the current
  vehicle back (`g_currentVehicle.refreshModel`).

The armor overlay of the client's armor screen is a CGF component (`ArmorInspectorComponent`) put on the hangar
vehicle, so the hits screen can show it without the Vehicle Hub.

## Logging

All modules log to the `sagtary.armor_hits` logger. The lines go to `game.log` in the game folder, for example
`[INFO] [Main] [SCRIPT] [sagtary.armor_hits] init v0.1.0`.
