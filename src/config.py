from logger import log

CONFIG = {
    # BASIC CONFIGURATION
    "ATTACK_KEY": "f1",
    "TELEPORT_KEY": "f2",
    "ATTACK_KEY2": "f3",
    "PORTAL_KEY": "f4",
    "ARMOR_KEY": "f5",
    "BATTLE_COMMAND": "f6",
    "BATTLE_ORDER": "f7",

    "POTION_BELT": "~",

    "TAKE_ALL": 1,

    "MANA_PERCENT_TO_DRINK_POTION": 40,
    "LIFE_PERCENT_TO_DRINK_POTION": 80,
    "LIFE_PERCENT_TO_DRINK_REJU": 20,

    "USE_MERC": 1,
    "MERC_LIFE_TO_DRINK_POTION": 70,

    "GAMES_MAX": 10000,
    "GAME_MAX_TIME": 300,
    "GAME_MIN_TIME": 95,
    "DIFFICULTY": "hell",
    "TASKS": ["Pindelskin"],
    # "TASKS": ["Mephisto"],

    # REGIONS
    "CENTER_LOCATION": (1280, 700),
    "MINIMAP_REGION": (0, 50, 860, 485),
    "MERC_REGION": (24, 21, 95, 122),
    "POTIONS_BAR_REGION": (1440, 1088, 312, 74),  # 4 bar
    "POTIONS_BAR_REGION2": (1440, 1160, 313, 70),  # 3 bar
    "POTIONS_HEALTH_REGION": (1438, 1086, 159, 76),
    "POTIONS_MANA_REGION": (1595, 1086, 156, 76),
    "TRADER_REGION": (0, 0, 930, 1140),
    "ITEMS_REGION": (1380, 0, 1142, 1440),
    "EQUIPMENT_REGION": (1769,676,289,288),
    "EMPTY_GOLD_REGION": (422,963,101,57),
    "GOLD_REGION": (305, 964, 57, 55),
    "CHAR_GOLD_REGION": (2007, 994, 55, 55),
    "STASH_BARS_REGION": (212, 247, 664, 53),
    "STASH_LOCATIONS": [(156,160), (332,162), (518,158), (700,161)],
    "TV_REGION": (1027, 603, 507, 187),
    "LOOT_REGION": (600, 150, 1700, 850),
    "WAYPOINT_REGION": (297, 46, 251, 86),
    "DEMON_REGION": (1140, 31, 272, 174),

    "MEPH_KILL_LOCATION": (760, 43),

    # COLORS
    "GREEN_TEXT": [0, 255, 0],
    "GREEN_TEXT2": [0, 252, 0],
    "WHITE_TEXT": [255, 255, 255],
    "BLUE_TEXT": [255, 110, 110],
    "GOLD_TEXT": [119, 179, 199],
    "RED_TEXT": [71, 71, 255],
    "ORANGE_TEXT": [0, 168, 255]
}


def main():
    log.info("Config test")


if __name__ == '__main__':
    main()
