# -*- coding: utf-8 -*-
"""Settings: ids, resource paths and texts."""

# User settings file, relative to the game folder (the client's working directory).
SETTINGS_PATH = 'mods/configs/sagtary_armor_hits/config.json'
DEFAULT_SETTINGS = {
    # Put the lobby button into the ModsList API mods list when ModsList API is installed;
    # false: always the button of its own in the hangar footer.
    'useModsList': True,
}

# Battle records (one JSON Lines file per battle), relative to the game folder.
RECORDS_DIR = 'mods/sagtary_armor_hits/battles'

# Battles of the session kept for the hits screen (in memory), newest first.
BATTLES_LIMIT = 50

# Developer tools on the hits screen: the Import and Export buttons, which read and write the battles of the screen
# to BATTLES_FILE, to test the screen without playing a battle first. Off in a release.
DEV_TOOLS = True
# Battles file of the developer tools, relative to the game folder.
BATTLES_FILE = 'mods/sagtary_armor_hits/battles.json'

# Id of the entry in the mods list (ModsList API, optional).
LOBBY_BUTTON_ID = 'sagtary_armor_hits'
# Path in the game resources; the file is resources/gui/maps/sagtary_armor_hits/icon.png in this repo.
LOBBY_BUTTON_ICON = 'gui/maps/sagtary_armor_hits/icon.png'

# Footer button (without ModsList API): name of its model for the script (ModelObserver), and its files.
FOOTER_BUTTON_MODEL = 'SagtaryArmorHitsFooterButton'
FOOTER_BUTTON_STYLE = 'coui://gui/gameface/mods/sagtary_armor_hits/FooterButton/FooterButton.css'
FOOTER_BUTTON_SCRIPT = 'coui://gui/gameface/mods/sagtary_armor_hits/FooterButton/FooterButton.js'

# The mod's own texts by client language, only those the client does not have; 'en' is used for a language that is
# not here.
TEXTS = {
    'en': {
        'lobbyButton/name': u'Armor Hits',
        'lobbyButton/description': u'Hits received and dealt in battle',
        'battles/empty': u'No battles yet',
        'hits/received': u'On me',
        'hits/dealt': u'By me',
    },
    'ru': {
        'lobbyButton/name': u'Armor Hits',
        'lobbyButton/description': u'Попадания по вам и ваши попадания в бою',
        'battles/empty': u'Боёв пока нет',
        'hits/received': u'По мне',
        'hits/dealt': u'По врагам',
    },
}
