# Armor Hits by Sagtary

A World of Tanks mod for the hangar: see where you were hit in battle and where you hit the enemies.

Work in progress. Now the mod:

- adds the **Armor Hits** button to the hangar; it opens the mod's own screen over the 3D hangar: the current
  vehicle, shown and turned like on the armor page, the battle selector with the battles and replays of this game
  session (kept in memory only), the hits on your vehicle and your hits in the selected battle, and the layout of the
  other panels;
- records every battle (and replay): each call from the server about shots and damage is written to a JSON Lines file
  in `<game>/mods/sagtary_armor_hits/battles/`, one file per battle. The files are not deleted by the mod, and they
  hold the names, account ids and clans of the players of the battle.

## Requirements

- World of Tanks EU client 2.4.1.0.
- [OpenWG Gameface](https://gitlab.com/openwg/wot.gameface) (`net.openwg.gameface`) for the button in the hangar
  footer, next to the game menu button.
- Optional: [ModsList API](https://gitlab.com/wot-public-mods/mods-list) (`me.poliroid.modslistapi`). When it is
  installed, the button is an entry in its mods list instead (Aslain's Mod Menu shows the same list). ModsList API
  itself needs OpenWG Gameface too.

| Installed                            | Button                                      |
|--------------------------------------|---------------------------------------------|
| OpenWG Gameface                      | in the hangar footer                        |
| OpenWG Gameface and ModsList API     | in the mods list (or footer, see Settings)  |
| neither                              | none, a warning in `game.log`               |

## Settings

`<game>/mods/configs/sagtary_armor_hits/config.json`, written with the defaults on the first start:

```json
{
    "useModsList": true
}
```

- `useModsList`: `true` puts the button into the ModsList API mods list when ModsList API is installed; `false`
  keeps it in the hangar footer always.

The file is read when the game starts; restart the game after a change.

## Build

Run with Python 2.7, the game's Python version:

```
C:\Python27\python.exe build.py            -> build/sagtary.armor_hits_<version>.wotmod
C:\Python27\python.exe build.py --install  -> also copy into <game>/mods/<client version>/
```

The game folder is `D:\programs\World_of_Tanks_EU`; set `WOT_DIR` for another one. The client version is read from
`version.xml` in the game folder.

## Layout

See [docs/architecture.md](docs/architecture.md).
