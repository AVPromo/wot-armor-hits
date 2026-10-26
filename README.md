# Armor Hits by Sagtary

A World of Tanks mod for the hangar: see every hit of your battles on the 3D vehicle, where you were hit and where
your shells went.

The mod adds the **Armor Hits** button to the hangar. It opens a screen like the game's armor page: the vehicle of the
battle in 3D, the list of its hits and the details of each one.

> [!IMPORTANT]
> **Found a bug or have an idea?**
> [Create an issue](https://github.com/pavel-bolhovitin/wot-armor-hits/issues/new/choose) and pick **Bug report** or
> **Idea**. Or write in the comments of the mod's page on WGMods.

## Installation

![Installation: copy the mods folder from the archive into the game folder](docs/install-guide.png)

Without the archive:

1. Install [OpenWG Gameface](https://gitlab.com/openwg/wot.gameface) and
   [ModsList API](https://gitlab.com/wot-public-mods/mods-list).
2. Copy `sagtary.armor_hits_<version>.wotmod` into `[WoT game directory]/mods/2.4.1.0/`.
3. Start the game. The **Armor Hits** button is in the hangar.

## Features

- **Battles**: the battles of this game session, newest first, up to 50, and the battles you saved to disk.
- **On me / By me**: the hits you received and the hits you dealt, with filters by result (damage, blocked,
  ricochet, no damage) and their counts.
- **The hit in 3D**: the vehicle with its turret and gun turned as at the moment of the hit, and the shell's way to
  the armor: a white line, dashes after a ricochet or spaced armor, rings pointing back to the shooter.
- **Lines**: the way of the chosen hit only, or of all hits on you at once.
- **Shooter view**: the camera looks along the shell, from the shooter's side.
- **Armor views** of the game: no armor, nominal armor, penetration; the game's armor tooltip under the mouse, for the
  shell of the chosen hit.
- **Details**: shooter and target, shell, result, damage, penetration, armor and impact angle, distance, damaged
  modules and crew.
- **Keep battles**: off, for the session or on disk, by groups of modes.

## Requirements

- World of Tanks EU client 2.4.1.0
- [OpenWG Gameface](https://gitlab.com/openwg/wot.gameface) (already in the archive, no need to download it)
- [ModsList API](https://gitlab.com/wot-public-mods/mods-list) (already in the archive, no need to download it)

## FAQ

**Why is my last battle not in the list?**
Its mode group is set to **Off** in **Keep battles**. By default only Random and Competitive battles are kept.

**I do not see the Armor Hits button.**
Check that OpenWG Gameface is installed for the same game version.

## Report a bug

1. [Create an issue](https://github.com/pavel-bolhovitin/wot-armor-hits/issues/new/choose) and pick **Bug report**.
2. Tell what you did, what you expected and what happened instead. A screenshot helps.
3. Attach `game.log` from the `[WoT game directory]` folder.
4. For a problem with the hits of a battle: turn on **Debug** in the settings, play such a battle again and attach
   its file from `[WoT game directory]/mods/sagtary_armor_hits/debug/`.

No GitHub account? Write in the comments of the mod's page on WGMods.

## For developers

Build with Python 2.7, the game's Python version:

```text
C:\Python27\python.exe build.py            # build/sagtary.armor_hits_<version>.wotmod
C:\Python27\python.exe build.py --install  # also copy it into <game>/mods/<client version>/
```

The game folder is `D:\programs\World_of_Tanks_EU`; set `WOT_DIR` for another one. The client version is read from
`version.xml` in the game folder.

The code layout is in [docs/architecture.md](docs/architecture.md).

## License

MIT, see [LICENSE](LICENSE).
