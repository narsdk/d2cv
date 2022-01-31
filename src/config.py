from logger import log

CONFIG = {
    "MINIMAP_REGION": (0, 50, 860, 485),
    "CENTER_LOCATION": (1280, 700),

    "TELEPORT_KEY": "f2",
    "ATTACK_KEY": "f1",
    "ATTACK_KEY2": "f6",
    "ARMOR_KEY": "f4",
    "PORTAL_KEY": "f5",

    "MANA_PERCENT_TO_DRINK_POTION": 10,
    "LIFE_PERCENT_TO_DRINK_POTION": 70,
    "LIFE_PERCENT_TO_DRINK_REJU": 20,

    "USE_MERC": 1,
    "MERC_LIFE_TO_DRINK_POTION": 60,

    "games_max": 10000,
    "difficulty": "hell"
}


def main():
    log.info("Config test")


if __name__ == '__main__':
    main()
