from logger import log
from pysikuli import Region
from src.config import CONFIG
from time import sleep
import cv2 as cv
import imutils
from difflib import SequenceMatcher
import pytesseract
from vlogging import VisualRecord
import re

# Download and install tesseract from https://github.com/UB-Mannheim/tesseract/wiki
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'


class LootCollector:
    def __init__(self):
        self.good_items = {}
        # Load items lists
        for item_rarity in ["unique", "set", "rune", "magic"]:
            with open("items/" + item_rarity + ".txt") as file:
                file_lines = [line.rstrip() for line in file]
                self.good_items[item_rarity] = [re.sub(r"(\w)([A-Z])", r"\1 \2", line.split(" ")[2])
                                                for line in file_lines if line.startswith("[Name]")]
                log.info("Item rarity {}:".format(item_rarity))
                log.info(self.good_items[item_rarity])

    @staticmethod
    def get_equipment_item():
        log.info("get_equipment_item start")
        occupied_equipment = Region(*CONFIG["EQUIPMENT_REGION"]).image_mask("images/empty_equipment.png", inverted=True)
        if occupied_equipment is None:
            log.info("No equipment found - None.")
            return None, None
        log.info(VisualRecord("Occupied equipment", [occupied_equipment], fmt="png"))
        cnts = cv.findContours(occupied_equipment.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        if not cnts:
            log.info("No equipment found.")
            return None, None
        c = max(cnts, key=cv.contourArea)

        item_x, item_y = tuple(c[c[:, :, 1].argmax()][0])
        item = item_x + CONFIG["EQUIPMENT_REGION"][0] + 30, item_y + CONFIG["EQUIPMENT_REGION"][1] - 30
        log.info("Found item on location: " + str(item))
        return item

    def item_classification(self, item_name, rarity):
        for good_item in self.good_items[rarity]:
            log.debug("Classification of {} compared to found item {}".format(good_item, item_name))
            similarity_ratio = SequenceMatcher(None, good_item.lower(), item_name.lower()).ratio()
            log.debug("Classification ratio: " + str(similarity_ratio))
            if similarity_ratio > 0.8:
                return True
        else:
            return False

    @staticmethod
    def get_item_region():
        screen = Region(*CONFIG["ITEMS_REGION"])
        screen.update_screen()
        masked_screen = screen.get_colored_mask([68, 68, 68])
        thresh = cv.threshold(masked_screen, 45, 255, cv.THRESH_BINARY)[1]
        cnts = cv.findContours(thresh.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        c = max(cnts, key=cv.contourArea)
        x, y, w, h = cv.boundingRect(c)
        x = x + 1380
        log.visual(VisualRecord("Item region", [screen, masked_screen], fmt="png"))

        log.debug("Found item contour: {},{},{},{}".format(x, y, w, h))

        return x, y, w, h

    @staticmethod
    def get_item_rarity(item_region):
        x, y, w, h = item_region
        item_name_region = x, y, w, 50
        item_name = Region(*item_name_region)

        if item_name.match_color([CONFIG["GOLD_TEXT"]], method="nonzero") is not None:
            rarity = "unique"
        elif item_name.match_color([CONFIG["GREEN_TEXT"]], method="nonzero") is not None:
            rarity = "set"
        elif item_name.match_color([CONFIG["ORANGE_TEXT"]], method="nonzero") is not None:
            rarity = "rune"
        elif item_name.match_color([CONFIG["BLUE_TEXT"]], method="nonzero") is not None:
            rarity = "magic"
        elif item_name.match_color([CONFIG["WHITE_TEXT"]], method="nonzero") is not None:
            rarity = "normal"
        else:
            rarity = "unknown"
        return rarity

    @staticmethod
    def get_item_description():
        item_region = LootCollector.get_item_region()
        screen = Region(*item_region)
        screen.update_screen()
        masked_screen = screen.get_colored_mask([CONFIG["GREEN_TEXT"], CONFIG["WHITE_TEXT"], CONFIG["BLUE_TEXT"],
                                                 CONFIG["GOLD_TEXT"], CONFIG["RED_TEXT"], CONFIG["ORANGE_TEXT"]])

        # Performing OTSU threshold
        ret, thresh1 = cv.threshold(masked_screen, 0, 255, cv.THRESH_OTSU | cv.THRESH_BINARY_INV)

        # Specify structure shape and kernel size.
        # Kernel size increases or decreases the area
        # of the rectangle to be detected.
        # A smaller value like (10, 10) will detect
        # each word instead of a sentence.
        rect_kernel = cv.getStructuringElement(cv.MORPH_RECT, (18, 18))

        # Applying dilation on the threshold image
        dilation = cv.dilate(thresh1, rect_kernel, iterations=1)

        # Finding contours
        contours, hierarchy = cv.findContours(dilation, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)

        # Creating a copy of image
        im2 = masked_screen.copy()

        # Looping through the identified contours
        # Then rectangular part is cropped and passed on
        # to pytesseract for extracting text from it
        # Extracted text is then written into the text file
        text = ""
        for cnt in contours:
            x, y, w, h = cv.boundingRect(cnt)

            # Drawing a rectangle on copied image
            cv.rectangle(im2, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Cropping the text block for giving input to OCR
            cropped = im2[y:y + h, x:x + w]

            # Apply OCR on the cropped image
            text += pytesseract.image_to_string(cropped)

            for c in "@®":
                text = text.replace(c, "O")

        # Get item rarity
        rarity = LootCollector.get_item_rarity(item_region)
        log.info("Item rarity: " + str(rarity))
        log.visual(VisualRecord("Rectangled", [im2], fmt="png"))
        log.debug("Full item description: " + str(text))
        return text, rarity


def main():
    log.info("Loot collector test")
    sleep(2)


if __name__ == '__main__':
    main()
