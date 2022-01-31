from logger import log, GameError
from abc import abstractmethod
from time import sleep
from src.config import CONFIG
import pyautogui as pyag


class Task:
    def __init__(self, name, character, looter, maptraveler):
        self.name = name
        self.looter = looter
        self.character = character
        self.maptraveler = maptraveler

    def execute(self):
        log.info("Starting task: " + self.name)
        self.pre_actions()
        self.approach()
        self.kill()
        self.post_actions()
        log.info("Finished " + self.name)

    @abstractmethod
    def pre_actions(self):
        pass

    @abstractmethod
    def approach(self):
        pass

    @abstractmethod
    def kill(self):
        pass

    @abstractmethod
    def post_actions(self):
        pass


class Pindelskin(Task):
    def pre_actions(self):
        pass

    def approach(self):
        pass

    def kill(self):
        pass

    def post_actions(self):
        pass

    def go_to_anya(self):
        log.info("Going to anya start")
        self.character.go_to_destination("images/anya.png", (100, 40))
        self.character.go_to_destination("images/anya.png", (20, 45), move_step=(400, 450))
        sleep(0.3)
        self.character.enter_destination(([0, 239, 239], [0, 243, 243]), "images/nihlak_portal.png",
                                         "images/ingame.png", special_shift=(-60, 0))

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

            diff_location_x, diff_location_y = self.maptraveler.get_diff_from_destination(([18, 160, 184],
                                                                                           [45, 184, 185]))
            if diff_location_x is None or diff_location_x > 3 or diff_location_y < -3:
                log.debug("Teleporting to pindle number " + str(tele_timeout))
                self.maptraveler.click(tele_click_location, button="right")
                sleep(0.1)
            else:
                log.debug("Teleporting to pindle completed.")
                return True


class Mephisto(Task):
    def pre_actions(self):
        pass

    def approach(self):
        pass

    def kill(self):
        pass

    def post_actions(self):
        pass


def main():
    log.info("Tasks test")


if __name__ == '__main__':
    main()
