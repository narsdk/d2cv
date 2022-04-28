from logger import log, GameError
from pysikuli import Region
from src.config import CONFIG
import pyautogui as pyag
from time import sleep
from maptraveler import MapTraveler
from character import Character
from loot_collector import LootCollector
from abc import abstractmethod
from stats import Statistics


class TownManager:
    def __init__(self, character, stats):
        self.character = character
        self.stats = stats
        self.pysikuli = Region()
        self.traveler = MapTraveler()
        self.loot_collector = LootCollector()
        self.act = None

    @abstractmethod
    def manage_merc(self):
        pass

    @abstractmethod
    def goto_shop(self):
        pass

    @abstractmethod
    def goto_stash(self):
        pass

    def goto_wp(self):
        Region().click("images/wp_act" + str(self.act) + ".png")

    def execute(self):
        self.pre_game_actions()
        self.goto_shop()
        self.goto_stash()
        self.store_items()
        self.manage_merc()
        self.goto_wp()

    def pre_game_actions(self):
        log.debug("Pre game actions.")
        # Activate minimap
        sleep(0.2)
        pyag.press('tab')
        sleep(0.2)
        # Activate armor
        pyag.press(CONFIG["ARMOR_KEY"])
        sleep(0.2)
        self.pysikuli.hover(CONFIG["CENTER_LOCATION"])
        sleep(0.2)
        pyag.click(button="right")
        sleep(0.2)
        pyag.press(CONFIG["TELEPORT_KEY"])
        sleep(0.2)
        # pick up corpse
        self.pickup_corpse()
        sleep(0.2)
        self.manage_potions()
        sleep(0.2)

    def pickup_corpse(self):
        log.debug("Pickup corpse start.")
        self.traveler.update_screen()
        corpse = self.traveler.match_color([[251, 0, 251], [255, 1, 255]], method="nonzero")
        if corpse is not None:
            log.info("Corpse found.")
            sleep(1)
            self.pysikuli.click((1301, 659))
            sleep(1)
            self.stats.corpses_collected += 1
        else:
            log.debug("Corpse not found.")

    def manage_potions(self):
        log.debug("Start manage potions.")
        pyag.press("i")
        manage_potions_timeout = 0
        while True:
            manage_potions_timeout += 1
            log.debug("Manage potions nr" + str(manage_potions_timeout))
            if manage_potions_timeout > 15:
                log.debug("Timeout when clearing eq from potions.")
                break
            if Region(*CONFIG["EQUIPMENT_REGION"]).exists("images/healing_potion.png", 0.3):
                log.debug("Moving health potion")
                Region(*CONFIG["EQUIPMENT_REGION"]).hover("images/healing_potion.png")
                with pyag.hold('shift'):
                    pyag.click()
                    sleep(0.1)
            elif Region(*CONFIG["EQUIPMENT_REGION"]).exists("images/mana_potion.png", 0.3):
                log.debug("Moving mana potion")
                Region(*CONFIG["EQUIPMENT_REGION"]).hover("images/mana_potion.png")
                with pyag.hold('shift'):
                    pyag.click()
                    sleep(0.1)
            else:
                log.debug("No more potions in equipment.")
                break

        pyag.press("i")

    def store_items(self):
        log.debug("Store items start")
        check_equipment = False
        if CONFIG["USE_MERC"]:
            if not Region(*CONFIG["MERC_REGION"]).exists("images/merc_exists.png", 0.2):
                check_equipment = True
        pyag.press("i")
        sleep(0.1)
        if self.loot_collector.get_equipment_item() != (None, None) or check_equipment:
            pyag.press("i")
            log.info("Some items to stash found.")

            self.character.enter_destination("images/stash.png", "images/stash_destination.png",
                                             "images/stash_inside.png", special_shift=(70, 200))

            # Switch to personal tab
            log.info("Enter personal tab.")
            self.pysikuli.click(CONFIG["STASH_LOCATIONS"][0])
            sleep(0.1)

            # Get gold from other stash bars if there are less than 100k in personal
            if Region(*CONFIG["EMPTY_GOLD_REGION"]).exists("images/emptygold.png", 0.1):
                log.info("Not enough gold. Gathering from other stash bars.")
                for bar_number in range(1, 3):
                    log.info("Switching stash bar to " + str(bar_number))
                    self.pysikuli.click(CONFIG["STASH_LOCATIONS"][bar_number])
                    sleep(0.1)
                    if not Region(*CONFIG["EMPTY_GOLD_REGION"]).exists("images/emptygold.png", 0.1):
                        log.info("Collecting gold from stash bar " + str(bar_number))
                        Region(*CONFIG["GOLD_REGION"]).click("images/windraw.png")
                        sleep(0.1)
                        for i in range(1, 8):
                            pyag.press("backspace")
                            sleep(0.02)
                        pyag.typewrite("400000")
                        pyag.press("enter")
                        log.info("Gold collected.")
                        break
                else:
                    log.error("Lack of gold. Exiting.")
                    exit(0)
                log.info("Sending gold to personal bar.")
                sleep(0.1)
                self.pysikuli.click(CONFIG["STASH_LOCATIONS"][0])
                sleep(0.1)
                Region(*CONFIG["CHAR_GOLD_REGION"]).click("images/windraw.png")
                sleep(0.1)
                pyag.press("enter")
                sleep(0.1)

            log.info("Start storing items.")
            items_storing_timeout = 0
            current_stash = 0
            previous_item_to_store = (None, None)
            while True:
                log.info("1")
                items_storing_timeout += 1
                if items_storing_timeout >= 16:
                    log.error("Timeout when storing items.")
                    raise GameError("Timeout when storing items.")

                item_to_store = self.loot_collector.get_equipment_item()
                log.info("2")
                if item_to_store == (None, None):
                    log.info("All items stored.")
                    pyag.press("esc")
                    break
                elif item_to_store == previous_item_to_store:
                    log.info("Stash bar is full, switching to next bar.")
                    previous_item_to_store = (None, None)
                    current_stash += 1
                    if current_stash > 3:
                        log.error("Whole stash is full. Exiting")
                        sleep(6000)
                        exit(0)
                    self.pysikuli.click(CONFIG["STASH_LOCATIONS"][current_stash])
                else:
                    log.info("Hovering item to store.")
                    self.pysikuli.hover(item_to_store)
                    sleep(0.2)
                    found_item_description, rarity = self.loot_collector.get_item_description()
                    log.info("Item description: " + str(found_item_description))
                    item_name = found_item_description.partition('\n')[0]
                    if rarity != "unknown" and self.loot_collector.item_classification(item_name, rarity):
                        self.stats.found_items_list.append(item_name)
                        log.info("Store item: " + str(item_name))
                        sleep(0.1)
                        with pyag.hold('ctrl'):
                            pyag.click()
                            sleep(0.1)
                    else:
                        self.stats.ignored_items_list.append(item_name)
                        log.info("Ignored item: " + str(item_name))
                        sleep(0.1)
                        pyag.click()
                        sleep(0.1)
                        self.pysikuli.hover(CONFIG["CENTER_LOCATION"])
                        pyag.click()
                        sleep(0.1)
                    previous_item_to_store = item_to_store
        else:
            pyag.press("i")
        log.info("Storing items finished.")

    def do_shopping(self):
        log.info("Start shopping.")
        self.pysikuli.click("images/trade.png")
        sleep(1)
        pyag.press(CONFIG["POTION_BELT"])
        sleep(0.2)
        while Region(*CONFIG["POTIONS_HEALTH_REGION"]).exists("images/empty_potion.png", 1):
            healing_potion_loc = Region(*CONFIG["TRADER_REGION"]).match_color([[0, 0, 168], [64, 62, 238]],
                                                                              method="nonzero")
            self.pysikuli.click(healing_potion_loc, button="right")
            sleep(0.2)
            self.stats.life_potions_bought += 1
        while Region(*CONFIG["POTIONS_MANA_REGION"]).exists("images/empty_potion.png", 0.3):
            mana_potion_loc = Region(*CONFIG["TRADER_REGION"]).match_color([[34, 0, 0], [72, 3, 4]],
                                                                           method="nonzero")
            self.pysikuli.click(mana_potion_loc, button="right")
            sleep(0.2)
            self.stats.mana_potions_bought += 1
        pyag.press("esc")

    def recognize_town(self):
        if Region().exists("images/act5.png", 0.5):
            log.info("Recognized Act 5.")
            return Act5(self.character, self.stats)
        elif Region().exists("images/act3.png", 0.5):
            log.info("Recognized Act 3.")
            return Act3(self.character, self.stats)
        else:
            log.error("ERROR: Unknown town.")
            raise GameError


class Act5(TownManager):
    def __init__(self, character, stats):
        super().__init__(character, stats)
        self.act = 5

    def manage_merc(self):
        if CONFIG["USE_MERC"]:
            log.debug("Manage merc start.")
            if not Region(*CONFIG["MERC_REGION"]).exists("images/merc_exists.png", 0.2):
                log.info("Merc do not found. Going to buy one.")
                self.character.go_to_destination("images/stash.png", (-80, 35), accepted_distance=15)
                self.character.go_to_destination("images/merc_trader.png", (0, 40))
                self.character.enter_destination("images/merc_trader.png", "images/merc_trader_destination.png",
                                                 "images/resurrect.png", special_shift=(70, 200))
                self.pysikuli.click("images/resurrect.png")
                sleep(0.2)
                pyag.press("esc")
                self.stats.merc_resurrected += 1
                self.character.go_to_destination("images/merc_trader.png", (50, 50))
                if not self.pysikuli.exists("images/stash.png", 0.3):
                    self.character.go_to_destination("images/merc_trader.png", (80, 50))
                self.character.go_to_destination("images/stash.png", (-80, 35), accepted_distance=15)

    def goto_shop(self):
        log.info("Going to Malah shop.")
        pyag.press(CONFIG["POTION_BELT"])
        if Region(*CONFIG["POTIONS_BAR_REGION2"]).exists("images/empty_potion.png", 0.2):
            log.info("Found some empty potion slots, going to Malah")
            pyag.press(CONFIG["POTION_BELT"])
            self.character.go_to_destination("images/malah.png", (10, 30))
            self.character.enter_destination("images/malah.png", "images/malah_destination.png", "images/trade.png",
                              special_shift=(70, 200))
            self.do_shopping()

            # go_to_destination("images/malah.png",(20,40),critical=False)
            # go_to_destination("images/malah.png", (70, 20),critical=False)
            sleep(0.1)
            self.pysikuli.click((1301, 1089))
            sleep(1)
            self.pysikuli.click((1676, 657))
            sleep(0.5)
            self.pysikuli.click((1676, 657))
            sleep(0.5)
            self.pysikuli.click((1676, 657))
            sleep(0.3)
        else:
            log.info("No empty potion slot find.")
            pyag.press(CONFIG["POTION_BELT"])

    def goto_stash(self):
        self.character.go_to_destination("images/stash.png", (-45, 5))


class Act3(TownManager):
    def __init__(self, character, stats):
        super().__init__(character, stats)
        self.act = 3

    def goto_shop(self):
        log.info("Going to Ormus shop.")
        self.character.go_to_destination("images/meshif.png", (80, 20))
        self.character.go_to_destination("images/ormus.png", (-10, 10))
        pyag.press(CONFIG["POTION_BELT"])
        if Region(*CONFIG["POTIONS_BAR_REGION2"]).exists("images/empty_potion.png", 0.2):
            log.info("Found some empty potion slots, going to Ormus")
            pyag.press(CONFIG["POTION_BELT"])
            self.character.enter_destination("images/ormus.png", "images/ormus_destination.png", "images/trade.png",
                                             special_shift=(70, 200))
            self.do_shopping()
        else:
            log.info("No empty potion slot find.")
            pyag.press(CONFIG["POTION_BELT"])

    def goto_stash(self):
        self.character.go_to_destination("images/decard.png", (0, 30))
        # if Region().exists("images/stasha3.png"):
        #
        # else:
        #     log.error("Cannot enter stash")

    def manage_merc(self):
        pass


def main():
    log.info("Town manager test")
    sleep(2)
    traveler = MapTraveler()
    character = Character(traveler)
    stats = Statistics()
    town_manager = TownManager(character, stats).recognize_town()
    town_manager.execute()


def storeitems_test():
    log.info("Town manager test")
    sleep(2)
    traveler = MapTraveler()
    stats = Statistics()
    character = Character(traveler)
    town_manager = Act5(character, stats)
    town_manager.store_items()


def gotostash_test():
    log.info("Go to stash")
    sleep(2)
    traveler = MapTraveler()
    stats = Statistics()
    character = Character(traveler)
    town_manager = Act5(character, stats)
    town_manager.goto_stash()


if __name__ == '__main__':
    #main()
    storeitems_test()
    #gotostash_test()
