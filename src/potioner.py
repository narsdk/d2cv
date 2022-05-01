import threading

from logger import log, GameError
from pysikuli import Region
from src.config import CONFIG
from time import sleep
import datetime
import cv2 as cv
import imutils
import random
import pyautogui as pyag
import keyboard
from vlogging import VisualRecord


class Potioner:
    def __init__(self):
        self.screen = Region()
        self.running = True

    # Drink potions when needed, started in thread
    def start(self):
        log.info("Start potioner thread.")
        healing_delay = 10   # wait 5 seconds after heal to heal again - workaround to not use all potions too fast
        merc_healed_time = datetime.datetime.now()
        char_healed_time = datetime.datetime.now()
        while True:
            potioner_loop_start = datetime.datetime.now()
            log.info("Running value is " + str(self.running))
            if not self.running:
                log.info("Finishing potioner.")
                break

            if Region(1055, 728, 452, 87).exists("images/continue.png", 0.03):
                log.error("You are dead!")
                sleep(1)
                self.screen.click("images/continue.png")
                raise GameError("Hero is dead.")

            if not Region(1229, 1284, 104, 121).exists("images/ingame.png", 1):
                log.warning("Cannot find ingame image. Waiting for it.")
                sleep(10)
                continue

            current_time = datetime.datetime.now()

            if CONFIG["USE_MERC"] and Region(*CONFIG["MERC_REGION"]).exists("images/merc_exists.png", 0.03):
                merc_life = self.get_merc_life()
                merc_heal_time_delay = current_time - merc_healed_time
                if merc_life < CONFIG["MERC_LIFE_TO_DRINK_POTION"] and merc_heal_time_delay.seconds > healing_delay:
                    log.info("Healing merc.")
                    with pyag.hold('shift'):
                        pyag.press(str(random.randint(1, 2)))
                    merc_healed_time = datetime.datetime.now()

            life_percent = self.get_resource("health")
            mana_percent = self.get_resource("mana")

            log.debug("Life: {}% Mana: {}%".format(life_percent, mana_percent))
            if life_percent == -1 or mana_percent == -1:
                log.error("Failed to get resources.")
                continue

            char_heal_time_delay = current_time - char_healed_time
            if life_percent < CONFIG["LIFE_PERCENT_TO_DRINK_POTION"] and char_heal_time_delay.seconds > healing_delay:
                log.info("Drinking health potion.")
                self.drink_potion("health")
                char_healed_time = datetime.datetime.now()
            if mana_percent < CONFIG["MANA_PERCENT_TO_DRINK_POTION"]:
                log.info("Drinking mana potion.")
                #self.drink_potion("mana")
            log.info("Potioner loop took " + str(datetime.datetime.now() - potioner_loop_start))
            sleep(0.3)

    # Dring mana or health potion
    def drink_potion(self, type):
        if type == "health":
            pyag.press(str(random.randint(1, 2)))
        elif type == "reju":
            pyag.press("2")
        elif type == "mana":
            pyag.press(str(random.randint(3, 4)))

    # POTIONER
    # Get mana or life amount
    def get_resource(self, resource_type):
        if resource_type == "health":
            region = (500, 1205, 240, 230)
            color1a = (0, 50, 20)
            color1b = (5, 255, 255)
            color2a = (175, 50, 20)
            color2b = (180, 255, 255)
        elif resource_type == "mana":
            region = (1815, 1205, 240, 230)
            color1a = (100, 150, 0)
            color1b = (140, 255, 255)
            color2a = (100, 150, 0)
            color2b = (140, 255, 255)
        else:
            log.error("Unknown resource type.")

        resource_bar = Region(*region).get_screen()
        resource_bar_hsv = cv.cvtColor(resource_bar, cv.COLOR_BGR2HSV)

        ## Gen lower mask (0-5) and upper mask (175-180) of RED
        mask1 = cv.inRange(resource_bar_hsv, color1a, color1b)
        mask2 = cv.inRange(resource_bar_hsv, color2a, color2b)

        ## Merge the mask and crop the red regions
        mask = cv.bitwise_or(mask1, mask2)
        filtered_bar = cv.bitwise_and(resource_bar, resource_bar, mask=mask)

        # convert the image to grayscale
        gray_image = cv.cvtColor(filtered_bar, cv.COLOR_BGR2GRAY)
        gray = cv.GaussianBlur(gray_image, (5, 5), 0)

        # threshold the image, then perform a series of erosions + dilations to remove any small regions of noise
        thresh1 = cv.threshold(gray, 5, 255, cv.THRESH_BINARY)[1]
        thresh2 = cv.erode(thresh1, None, iterations=2)
        thresh = cv.dilate(thresh2, None, iterations=2)

        # find contours in thresholded image, then grab the largest
        # one
        cnts = cv.findContours(thresh.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        if not cnts:
            log.warning("Cannot find resource contours.")
            return -1

        c = max(cnts, key=cv.contourArea)

        extTop = tuple(c[c[:, :, 1].argmin()][0])

        log.debug("Top bar value: " + str(extTop))
        _, top_y = extTop

        resource = 100 - (top_y / 2.3)

        log.debug("Resource: " + str(resource_type) + " value is " + str(resource))
        return resource


    def get_merc_life(self):
        merc_screen = Region(*CONFIG["MERC_REGION"]).get_screen()
        green_mask = cv.inRange(merc_screen, (0, 100, 0), (8, 132, 24)) # cv.inRange(merc_screen, (0, 126, 0), (0, 126, 0))
        yellow_mask = cv.inRange(merc_screen, (32, 132, 208), (32, 132, 208)) # cv.inRange(merc_screen, (27, 126, 205), (27, 126, 205))
        red_mask = cv.inRange(merc_screen, (0, 44, 252), (0, 44, 252)) # cv.inRange(merc_screen, (23, 3, 239), (23, 3, 239))

        ## Merge the mask and crop the red regions
        mask = cv.bitwise_or(green_mask, yellow_mask, red_mask)
        filtered_bar = cv.bitwise_and(merc_screen, merc_screen, mask=mask)

        # convert the image to grayscale
        gray_image = cv.cvtColor(filtered_bar, cv.COLOR_BGR2GRAY)

        log.debug(VisualRecord("merc_screen / filtered_bar / gray_image", [merc_screen, filtered_bar, gray_image], fmt="png"))

        # find contours in thresholded image, then grab the largest one
        cnts = cv.findContours(gray_image.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        if not cnts:
            log.warning("Cannot find resource contours.")
            return -1

        c = max(cnts, key=cv.contourArea)

        extright = tuple(c[c[:, :, 0].argmax()][0])

        right_x, _ = extright
        merc_life = right_x * 1.16
        log.debug("Merc life: " + str(merc_life))
        return merc_life


def main():
    log.info("Potioner test")
    running = False
    potioner = Potioner()
    while True:
        if keyboard.is_pressed("ctrl+shift+c") and not running:
            log.info("Starting potioner thread.")
            sleep(1)
            running = True
            potioner_thread = threading.Thread(target=potioner.start)
            potioner_thread.daemon = True
            potioner_thread.start()
            log.info("Potioner thread started.")
            # 10 second test for performance purposes
            # sleep(10)
            # running = potioner.running = False
            # potioner_thread.join()
            # log.info("Potioner thread finished.")
        elif keyboard.is_pressed("ctrl+shift+c") and running:
            log.info("Finishing potioner thread.")
            sleep(1)
            running = potioner.running = False
            potioner_thread.join()
            log.info("Potioner thread finished.")


if __name__ == '__main__':
    main()
