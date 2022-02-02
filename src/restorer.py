from logger import log, GameError
from pysikuli import Region
from src.config import CONFIG
from time import sleep
import datetime
import cv2 as cv
import pyautogui as pyag


class Restorer:
    def __init__(self):
        self.screen = Region()

    # Restore game after crash
    def game_restore(self):
        log.info("Game restoring start")
        if not self.screen.exists("images/play.png", 1):
            restore_timeout = 0
            while True:
                restore_timeout += 1
                if restore_timeout % 5 == 0:
                    log.info("Alt+F4 as loading found")
                    with pyag.hold('alt'):
                        pyag.press("f4")
                    sleep(10)
                    pyag.press("up")
                    sleep(2)
                    pyag.press("enter")
                    sleep(10)
                if restore_timeout > 100:
                    log.info("Fatal error: cannot find launcher")
                    exit(1)
                # launcher = get_color_location([255, 224, 116], region=(438,1399,151,41))
                # if launcher != (None, None):
                log.info("Clicking launcher")
                self.screen.click((513, 1416))
                sleep(2)

                graj = Region(342, 899, 530, 396).get_color_location([255, 224, 116])
                if graj != (None, None):
                    log.info("Clicking graj")
                    graj_x, graj_y = graj
                    graj = (graj_x - 100, graj_y)
                    Region(342, 899, 530, 396).click(graj)
                    sleep(2)
                    break
                else:
                    log.error("Cannot find graj")
                    sleep(30)

            while not self.screen.exists("images/play.png", 10):
                log.info("Waiting for play image.")
                sleep(20)
                pyag.press("space")

            log.info("Restoring game success.")
        else:
            log.info("Play exists?")


def main():
    log.info("Potioner test")
    sleep(2)


if __name__ == '__main__':
    main()
