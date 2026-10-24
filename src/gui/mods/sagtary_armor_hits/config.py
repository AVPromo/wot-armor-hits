# -*- coding: utf-8 -*-
"""Settings: ids, resource paths and texts."""

# User settings file, relative to the game folder (the client's working directory).
SETTINGS_PATH = 'mods/configs/sagtary_armor_hits/config.json'
DEFAULT_SETTINGS = {
    # Put the lobby button into the ModsList API mods list when ModsList API is installed;
    # false: always the button of its own in the hangar footer.
    'showButtonInModsMenu': True,
    # Write the debug record of every battle (every server call about shots, one JSON Lines file per battle in
    # RECORDS_DIR) and the mod's info lines into the client's log (calls, checks, the hits of a battle); without it the
    # log has the mod's start, its battle files, its warnings and errors only.
    'debug': False,
    # Show the hits on allies (and of allies on the player) in the hits list; they do no damage.
    'showFriendlyFire': False,
    # Save every battle played (not a replay) to its battle file in BATTLE_FILES_DIR when the player leaves it, as the
    # save button does.
    'autoSaveBattles': False,
}

# Debug records (one JSON Lines file per battle), relative to the game folder.
RECORDS_DIR = 'mods/sagtary_armor_hits/debug'

# Battles of the session kept for the hits screen (in memory), newest first.
BATTLES_LIMIT = 50

# Folder of the battle files of the hits screen's save button (one file per battle, a player sends it with a report;
# the files put there are loaded when the hangar shows first), relative to the game folder.
BATTLE_FILES_DIR = 'mods/sagtary_armor_hits/hits'

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
        'lines/current': u'Current',
        'camera/shooter': u'Shooter view',
        'camera/reset': u'Reset',
        'file/save': u'Save battle',
        'file/delete': u'Delete battles',
        'file/deleteConfirm': u'Delete all battles and their files?',
        'file/deleted': u'Armor Hits: battles deleted',
        'file/exported': u'Armor Hits: battle saved to %(path)s',
        'file/failed': u'Armor Hits: %(error)s',
        'shot/shooter': u'Shooter',
        'shot/target': u'Target',
        'shot/damage': u'Damage',
        'shot/penetration': u'Penetration',
        'shot/armor': u'Armor',
        'shot/angle': u'Impact angle',
        'shot/distance': u'Distance',
        'shot/crits': u'Modules and crew',
        'shot/avgDamage': u'average shell damage',
        'shot/avgPenetration': u'average shell penetration',
        'shot/chance': u'penetration chance',
        'shot/nominal': u'nominal',
        'shot/angleArmor': u'armor from the angle',
        'shot/ricochet': u'ricochet',
        'shot/distanceLoss': u'for the distance of %(distance)s m',
        'shot/deviation': u'from the average',
        'settings/showFriendlyFire': u'Show friendly fire',
        'settings/autoSaveBattles': u'Save battles automatically',
        'settings/showButtonInModsMenu': u'Show the button in the mods menu',
        'settings/debug': u'Debug',
        'settings/restart': u'(game restart required)',
    },
    'ru': {
        'lobbyButton/name': u'Armor Hits',
        'lobbyButton/description': u'Попадания по вам и ваши попадания в бою',
        'battles/empty': u'Боёв пока нет',
        'hits/received': u'По мне',
        'hits/dealt': u'По врагам',
        'lines/current': u'Текущая',
        'camera/shooter': u'Вид стрелка',
        'camera/reset': u'Сброс',
        'file/save': u'Сохранить бой',
        'file/delete': u'Удалить бои',
        'file/deleteConfirm': u'Удалить все бои и их файлы?',
        'file/deleted': u'Armor Hits: бои удалены',
        'file/exported': u'Armor Hits: бой сохранён в %(path)s',
        'file/failed': u'Armor Hits: %(error)s',
        'shot/shooter': u'Стрелок',
        'shot/target': u'Цель',
        'shot/damage': u'Урон',
        'shot/penetration': u'Пробитие',
        'shot/armor': u'Броня',
        'shot/angle': u'Угол попадания',
        'shot/distance': u'Дистанция',
        'shot/crits': u'Модули и экипаж',
        'shot/avgDamage': u'средний урон снаряда',
        'shot/avgPenetration': u'среднее пробитие снаряда',
        'shot/chance': u'шанс пробития',
        'shot/nominal': u'номинальная',
        'shot/angleArmor': u'броня за счёт угла',
        'shot/ricochet': u'рикошет',
        'shot/distanceLoss': u'за дистанцию %(distance)s м',
        'shot/deviation': u'от среднего',
        'settings/showFriendlyFire': u'Показывать огонь по своим',
        'settings/autoSaveBattles': u'Автоматически сохранять бои',
        'settings/showButtonInModsMenu': u'Показывать кнопку в меню модов',
        'settings/debug': u'Дебаг',
        'settings/restart': u'(требуется перезапуск игры)',
    },
}
