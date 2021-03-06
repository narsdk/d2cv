from logger import log, GameError
from pysikuli import Region
from src.config import CONFIG
from time import sleep
import cv2 as cv
import imutils
import pyautogui as pyag
from vlogging import VisualRecord


class Pickit:
    def __init__(self):
        self.screen = Region(*CONFIG["LOOT_REGION"])

    def collect(self):
        log.info("Collect loot start")

        collect_timeout = 0
        self.screen.hover((50, 50))
        pyag.press("alt")
        sleep(0.3)
        while True:
            collect_timeout += 1
            if collect_timeout >= 10:
                log.error("Timeout when collecting loot.")
                raise GameError("Timeout when collecting loot.")

            self.screen.update_screen()
            gray_image = self.screen.get_colored_mask([CONFIG["ORANGE_TEXT"], CONFIG["GREEN_TEXT2"],
                                                       CONFIG["GOLD_TEXT"]], mask_filter=True)

            # threshold the image, then perform a series of erosion + dilatation to remove any small regions of noise
            thresh = cv.threshold(gray_image, 5, 255, cv.THRESH_BINARY)[1]

            log.info(VisualRecord("Items", [self.screen.screen, gray_image, thresh], fmt="png"))
            # find contours in thresholded image, then grab the largest one
            cnts = cv.findContours(thresh.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)

            if not cnts:
                # Checking charms
                charm = self.screen.match("images/charm.png", threshold=0.6)
                if charm is None:
                    log.info("No more items found.")
                    pyag.press("alt")
                    break
                else:
                    item, _, _ = charm
            else:
                c = max(cnts, key=cv.contourArea)

                item_x, item_y = tuple(c[c[:, :, 1].argmax()][0])
                item = item_x + 600, item_y + 150

            log.info("Collecting item on location: " + str(item))
            self.screen.click(item)
            sleep(2)


def main():
    log.info("Pickit test")
    # Put some items on ground and run
    sleep(2)
    pickit = Pickit()
    pickit.collect()


if __name__ == '__main__':
    main()
