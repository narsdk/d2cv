from logger import log

CONFIG = {
    # BASIC CONFIGURATION
    "TELEPORT_KEY": "f2",
    "ATTACK_KEY": "f1",
    "ATTACK_KEY2": "f6",
    "ARMOR_KEY": "f5",
    "PORTAL_KEY": "f4",
    "POTION_BELT": "k",

    "MANA_PERCENT_TO_DRINK_POTION": 10,
    "LIFE_PERCENT_TO_DRINK_POTION": 70,
    "LIFE_PERCENT_TO_DRINK_REJU": 20,

    "USE_MERC": 1,
    "MERC_LIFE_TO_DRINK_POTION": 60,

    "GAMES_MAX": 10000,
    "DIFFICULTY": "hell",

    # REGIONS
    "CENTER_LOCATION": (1280, 700),
    "MINIMAP_REGION": (0, 50, 860, 485),
    "MERC_REGION": (24, 21, 95, 122),
    "POTIONS_BAR_REGION": (1450, 1122, 325, 77),  # 4 bar
    "POTIONS_BAR_REGION2": (1450, 1277, 325, 77),  # 2 bar
    "POTIONS_HEALTH_REGION": (1448, 1122, 163, 79),
    "POTIONS_MANA_REGION": (1613, 1122, 161, 77),
    "TRADER_REGION": (0, 0, 930, 1140),
    "ITEMS_REGION": (1380, 0, 1142, 1440),
    "EQUIPMENT_REGION": (1691, 736, 262, 263),
    "EMPTY_GOLD_REGION": (567, 1008, 20, 36),
    "GOLD_REGION": (419, 984, 252, 75),
    "CHAR_GOLD_REGION": (1895, 1015, 250, 68),
    "STASH_BARS_REGION": (212, 247, 664, 53),
    "STASH_LOCATIONS": [(296, 271), (460, 271), (626, 268), (794, 266)],
    "TV_REGION": (1027, 603, 507, 187),

    # COLORS
    "GREEN_TEXT": [0, 255, 0],
    "WHITE_TEXT": [255, 255, 255],
    "BLUE_TEXT": [255, 104, 104],
    "GOLD_TEXT": [113, 175, 196],
    "RED_TEXT": [71, 71, 255],
    "ORANGE_TEXT": [0, 163, 255]
}


def main():
    log.info("Config test")


if __name__ == '__main__':
    main()
