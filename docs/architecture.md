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

Planned, as the features come (after Poliroid's Battle Hits, which does the same job):

| Part              | Will do                                                                     |
|-------------------|-----------------------------------------------------------------------------|
| battle recording  | in battle, collect the hits received and dealt: shell, point, angle, result |
| storage           | keep the hits of the last battles between sessions                          |
| hangar scene      | show the vehicle in the hangar with the hit points on its armor             |
| viewer screen     | list of battles and hits; opened by the lobby button                        |

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

## Logging

All modules log to the `sagtary.armor_hits` logger. The lines go to `game.log` in the game folder, for example
`[INFO] [Main] [SCRIPT] [sagtary.armor_hits] init v0.1.0`.
