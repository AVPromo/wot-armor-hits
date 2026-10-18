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

# Battles of the session kept for the hits screen (in memory only), newest first.
BATTLES_LIMIT = 50

# Id of the entry in the mods list (ModsList API, optional).
LOBBY_BUTTON_ID = 'sagtary_armor_hits'
# Path in the game resources; the file is resources/gui/maps/sagtary_armor_hits/icon.png in this repo.
LOBBY_BUTTON_ICON = 'gui/maps/sagtary_armor_hits/icon.png'

# Footer button (without ModsList API): name of its model for the script (ModelObserver), and its files.
FOOTER_BUTTON_MODEL = 'SagtaryArmorHitsFooterButton'
FOOTER_BUTTON_STYLE = 'coui://gui/gameface/mods/sagtary_armor_hits/FooterButton/FooterButton.css'
FOOTER_BUTTON_SCRIPT = 'coui://gui/gameface/mods/sagtary_armor_hits/FooterButton/FooterButton.js'

# Texts by client language; 'en' is used for a language that is not here.
TEXTS = {
    'en': {
        'lobbyButton/name': u'Armor Hits',
        'lobbyButton/description': u'Hits received and dealt in battle',
        'battles/empty': u'No battles yet: play a battle or watch a replay',
        'battles/list': u'Recent battles',
    },
    'ru': {
        'lobbyButton/name': u'Armor Hits',
        'lobbyButton/description': u'Попадания по вам и ваши попадания в бою',
        'battles/empty': u'Боёв пока нет: сыграйте бой или откройте реплей',
        'battles/list': u'Последние бои',
    },
}
