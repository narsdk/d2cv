from logger import log, GameError
from abc import abstractmethod
from time import sleep
from src.config import CONFIG
import pyautogui as pyag
from vlogging import VisualRecord
from character import Character
from maptraveler import MapTraveler
from pickit import Pickit


class Task:
    def __init__(self, character, maptraveler):
        self.pickit = Pickit
        self.character = character
        self.maptraveler = maptraveler

    def execute(self):
        self.reach_location()
        self.pre_actions()
        self.approach()
        self.kill()
        self.pickit.collect()
        self.post_actions()

    @abstractmethod
    def reach_location(self):
        pass

    @abstractmethod
    def pre_actions(self):
        self.use_cta()

    @abstractmethod
    def approach(self):
        pass

    @abstractmethod
    def kill(self):
        pass

    @abstractmethod
    def post_actions(self):
        pass

    def goto_wp(self, waypoint):
        pass

    def use_cta(self):
        log.info("Using CTA.")
        sleep(0.3)
        pyag.press("w")
        sleep(0.3)
        pyag.press("f5")
        sleep(0.3)
        self.maptraveler.click(None, button="right")
        sleep(0.3)
        pyag.press("f6")
        sleep(0.3)
        self.maptraveler.click(None, button="right")
        sleep(0.3)
        pyag.press("f7")
        sleep(0.3)
        self.maptraveler.click(None, button="right")
        sleep(0.3)
        pyag.press("w")
        sleep(0.3)


class Pindelskin(Task):
    def reach_location(self):
        self.go_to_anya()

    def pre_actions(self):
        super().pre_actions()

    def approach(self):
        self.tele_to_pindle()

    def kill(self):
        log.info("Killing pindle start.")
        pyag.press(CONFIG["ATTACK_KEY"])
        sleep(0.1)
        self.maptraveler.click((1543, 575), button="right")
        sleep(0.2)
        pyag.press(CONFIG["ATTACK_KEY2"])
        for i in range(1, 6):
            self.maptraveler.click((1480, 543), button="right")
        pyag.press(CONFIG["ATTACK_KEY"])
        sleep(0.3)
        self.maptraveler.click((1788, 438), button="right")
        pyag.press(CONFIG["ATTACK_KEY2"])
        for i in range(1, 12):
            log.info("Attack nr " + str(i))
            if i % 6 == 0:
                pyag.press(CONFIG["ATTACK_KEY"])
            if i % 2 == 0:
                self.maptraveler.click((1480, 543), button="right")
            elif i % 2 == 1:
                self.maptraveler.click((1550, 613), button="right")
            if i % 6 == 0:
                pyag.press(CONFIG["ATTACK_KEY2"])

    def post_actions(self):
        pass

    def go_to_anya(self):
        log.info("Going to anya start")
        self.character.go_to_destination("images/anya.png", (100, 40))
        self.character.go_to_destination("images/anya.png", (20, 45), move_step=(400, 450))
        sleep(0.5)
        self.character.enter_destination(([0, 239, 239], [0, 243, 243]), "images/nihlak_portal.png",
                                         "images/ingame.png", special_shift=(0, 0))

    # TODO: Teleporting should be done by unified character moving methods
    def tele_to_pindle(self):
        log.info("Teleporting to pindle start.")
        tele_timeout = 0
        pyag.press(CONFIG["TELEPORT_KEY"])
        sleep(0.1)
        tele_click_location = (2080, 95)

        while True:
            tele_timeout += 1

            # Workaround - 3 teleportation are enough and changing entrance location sometimes doesnt works
            if tele_timeout >= 4:
                log.info("Teleporting to pindle completed.")
                return True

            if tele_timeout >= 10:
                log.error("Timeout when teleporting to pindle.")
                raise GameError("Timeout when teleporting to pindle.")

            diff_location = self.maptraveler.get_diff_from_destination(([18, 160, 184],[45, 184, 185]))
            if diff_location is not None:
                diff_location_x, diff_location_y = diff_location
            if diff_location is None or diff_location_x > 3 or diff_location_y < -3:
                log.debug("Teleporting to pindle number " + str(tele_timeout))
                self.maptraveler.click(tele_click_location, button="right")
                sleep(0.3)
            else:
                log.debug("Teleporting to pindle completed.")
                return True


class Mephisto(Task):
    def reach_location(self):
        self.goto_wp((3, 9))

    def pre_actions(self):
        super().pre_actions()

    def approach(self):
        self.find_meph_level()
        self.go_to_mephisto()

    def kill(self):
        pass

    def post_actions(self):
        pass

    def find_meph_level(self):
        log.info("Find meph tele direction.")
        pyag.press(CONFIG["TELEPORT_KEY"])
        self.character.teleport_to("tl", 600, sleep_time=0.3)
        self.character.teleport_to("dr", 600, sleep_time=0.3)
        self.character.teleport_to("dr", 600, sleep_time=0.3)
        self.character.teleport_to("tl", 600, sleep_time=0.3)
        self.character.teleport_to("tr", 600, sleep_time=0.3)
        self.character.teleport_to("dl", 600, sleep_time=0.3)
        self.character.teleport_to("dl", 600, sleep_time=0.3)
        self.character.teleport_to("tr", 600, sleep_time=0.3)

        self.maptraveler.update_screen()
        start_direction = self.maptraveler.get_start_direction()
        log.info("Start direction is " + start_direction)

        self.maptraveler.get_map_walls(mode="full")

        current_direction = start_direction
        tele_number = 0
        last_moves = []
        while True:
            tele_number += 1
            log.debug("Start teleporting number " + str(tele_number))
            log.info("Last moves: " + str(last_moves[-30:]))

            # Check if character stuck in loop
            last10 = last_moves[-10:]
            last50 = last_moves[-50:]
            if len([last10 for idx in range(len(last50)) if last50[idx: idx + len(last50)] == last10]) > 3:
                log.error("Character stuck. Trying some random teleports.")

            if tele_number >= 1000:
                log.error("Timeout when teleporting.")
                raise GameError("Timeout when teleporting.")

            self.character.teleport_to(current_direction, 650, sleep_time=0.3, mode="continuous")
            # sleep(0.18)

            log.debug("Getting new minimap")
            self.maptraveler.update_screen()
            log.visual(
                VisualRecord("New minimap", [self.maptraveler.screen], fmt="png"))
            log.debug("Minimap transformation")
            self.maptraveler.get_map_walls(mode="full")

            if self.maptraveler.get_entrance_location() is not None:
                entrance_result, known_entrance = self.character.goto_entrance()
                if entrance_result:
                    log.info("Mephisto level found.")
                    break
            else:
                current_direction, last_moves = self.maptraveler.find_new_direction(current_direction, last_moves)

    def meph_bait(self):
        sleep(0.3)
        self.character.go_to_destination(([170, 39, 82], [186, 75, 175]), (-85, -40), map_filter=True,
                                         accepted_distance=10, button="right")
        sleep(0.7)
        self.character.go_to_destination(([170, 39, 82], [186, 75, 175]), (-85, 0), map_filter=True,
                                         accepted_distance=10)
        sleep(0.7)
        self.character.go_to_destination(([170, 39, 82], [186, 75, 175]), (-50, 30), map_filter=True,
                                         accepted_distance=10, button="right")
        sleep(1)
        self.character.go_to_destination(([170, 39, 82], [186, 75, 175]), (-48, 50), map_filter=True,
                                         accepted_distance=7, move_sleep=0.7, move_step=(60, 100))

    def go_to_mephisto(self):
        for i in range(1, 9):
            self.character.teleport_to("tl", 800, sleep_time=0.3, offset=(0, 450))
        self.meph_bait()


def main():
    log.info("Tasks test")
    # Go to act 3 meph wp and start
    sleep(2)
    traveler = MapTraveler()
    character = Character(traveler)
    task = Pindelskin(character, traveler)
    task.tele_to_pindle()


if __name__ == '__main__':
    main()
