from logger import log, GameError
from pysikuli import Region
from src.config import CONFIG
import pyautogui as pyag
from time import sleep
from maptraveler import MapTraveler
from character import Character
from abc import abstractmethod
import cv2 as cv
import imutils
from difflib import SequenceMatcher

class LootCollector:
    def __init__(self):
        pass

    def get_equipment_item(self):
        log.debug("get_equipment_item start")
        occupied_equipment = Region(CONFIG["EQUIPMENT_REGION"]).image_mask("images/empty_equipment.png", inverted=True)
        cnts = cv.findContours(occupied_equipment.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        if not cnts:
            log.info("No equipment found.")
            return None, None
        c = max(cnts, key=cv.contourArea)

        item_x, item_y = tuple(c[c[:, :, 1].argmax()][0])
        item = item_x + 1696, item_y + 731
        log.info("Found item on location: " + str(item))
        return item

    def item_classification(self, item_name, rarity):
        global good_items
        for good_item in good_items[rarity]:
            log.info("Classification of {} compared to found item {}".format(good_item, item_name))
            similarity_ratio = SequenceMatcher(None, good_item.lower(), item_name.lower()).ratio()
            log.info("Classification ratio: " + str(similarity_ratio))
            if similarity_ratio > 0.8:
                return True
        else:
            return False

    def get_item_region(self):
        screen = get_screen(part=(1380, 0, 1142, 1440))
        masked_screen = multimask(screen, [62, 62, 62])
        img_gray = cv.cvtColor(masked_screen, cv.COLOR_BGR2GRAY)
        thresh = cv.threshold(img_gray, 45, 255, cv.THRESH_BINARY)[1]
        cnts = cv.findContours(thresh.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        c = max(cnts, key=cv.contourArea)
        x, y, w, h = cv.boundingRect(c)
        x = x + 1380

        log.debug("Found item contour: {},{},{},{}".format(x, y, w, h))

        return x, y, w, h

    def get_item_rarity(self, item_region):
        x, y, w, h = item_region
        item_name_region = x, y, w, 50

        if get_color_location([GOLD_TEXT], region=item_name_region) != (None, None):
            rarity = "unique"
        elif get_color_location([GREEN_TEXT], region=item_name_region) != (None, None):
            rarity = "set"
        elif get_color_location([ORANGE_TEXT], region=item_name_region) != (None, None):
            rarity = "rune"
        elif get_color_location([BLUE_TEXT], region=item_name_region) != (None, None):
            rarity = "magic"
        else:
            rarity = "unknown"
        return rarity

    # LOOT_COLLECTOR
    def get_item_description(self):
        item_region = get_item_region()
        screen = get_screen(part=(item_region))
        masked_screen = multimask(screen, [GREEN_TEXT, WHITE_TEXT, BLUE_TEXT, GOLD_TEXT, RED_TEXT, ORANGE_TEXT])
        gray = cv.cvtColor(masked_screen, cv.COLOR_BGR2GRAY)

        # Performing OTSU threshold
        ret, thresh1 = cv.threshold(gray, 0, 255, cv.THRESH_OTSU | cv.THRESH_BINARY_INV)

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
        im2 = gray.copy()

        # Looping through the identified contours
        # Then rectangular part is cropped and passed on
        # to pytesseract for extracting text from it
        # Extracted text is then written into the text file
        text = ""
        for cnt in contours:
            x, y, w, h = cv.boundingRect(cnt)

            # Drawing a rectangle on copied image
            rect = cv.rectangle(im2, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Cropping the text block for giving input to OCR
            cropped = im2[y:y + h, x:x + w]

            # Apply OCR on the cropped image
            text += pytesseract.image_to_string(cropped)

            for c in "@®":
                text = text.replace(c, "O")

        # Get item rarity
        rarity = self.get_item_rarity(item_region)
        log.info("Item rarity: " + str(rarity))

        log.debug("Full item description: " + str(text))
        return text, rarity

def main():
    log.info("Loot collector test")
    sleep(2)


if __name__ == '__main__':
    main()