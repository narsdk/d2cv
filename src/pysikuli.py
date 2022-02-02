from vlogging import VisualRecord
from logger import log
import ctypes
import cv2 as cv
import pyautogui as pyag
import numpy as np
from math import floor
from time import sleep
import datetime
import imutils

user32 = ctypes.windll.user32
SCREENRES_X, SCREENRES_Y = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

pyag.PAUSE = 0.03
MATCH_INTERVAL = 0.01


class Region:
    """
    Class Region: contains rectangle which is a ROI of screen. It makes screenshots of ROI and do some actions
    based on RainMan SikuliX on them - like checking if some images exists on screenshot and returning its
    location.
    """
    def __init__(self, x=0, y=0, w=SCREENRES_X, h=SCREENRES_Y):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.screen = None
        self.previous_screen = None
        self.last_match = None
        self.update_screen()

    # Return screenshot saved
    def get_screen(self):
        if self.screen is None:
            self.update_screen()
        return self.screen

    def get_previous_screen(self):
        return self.previous_screen

    # Collect screenshots of ROI
    def update_screen(self, png=None):
        if png:
            # Load image from file
            screen = cv.imread(png, cv.IMREAD_UNCHANGED)
        else:
            screen = pyag.screenshot(region=(self.x, self.y, self.w, self.h))
        self.previous_screen = self.screen
        self.screen = cv.cvtColor(np.array(screen), cv.COLOR_RGB2BGR)

    @staticmethod
    def compare_screens(img1, img2):
        # Compare images
        screens_diff = np.sum((img2.astype("float") - img1.astype("float")) ** 2)
        screens_diff /= float(img2.shape[0] * img2.shape[1])
        log.debug(VisualRecord(("Difference is: {}".format(screens_diff)), [img2, img1],
                               fmt="png"))
        return screens_diff

    def match(self, image, threshold=0.7, update=True):
        if self.screen is None or update:
            self.update_screen()

        log.debug("Matching image " + str(image))

        img = cv.imread(image, cv.IMREAD_UNCHANGED)
        img = cv.cvtColor(img, cv.COLOR_RGB2BGR)

        screenshot = self.screen.copy()

        res = cv.matchTemplate(img, screenshot, cv.TM_CCOEFF_NORMED)

        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
        log.debug("Best match location: {} similarity: {}".format(max_loc, max_val))

        if max_val > threshold:
            log.debug("Image matched")

            # Creating rectangle
            top_left = max_loc
            image_h, image_w, image_c = img.shape
            log.debug("Image height: " + str(image_h) + " Image width: " + str(image_w))
            location_x, location_y = top_left
            bottom_right = (location_x + image_w, location_y + image_h)
            img_rectangled = cv.rectangle(screenshot, top_left, bottom_right, color=(0, 255, 0), thickness=2,
                                          lineType=cv.LINE_4)

            # Creating center point
            center_x = location_x + floor(image_w / 2)
            center_y = location_y + floor(image_h / 2)
            center_loc = (center_x + self.x, center_y + self.y)
            img_final = cv.circle(img_rectangled, center_loc, radius=0, color=(0, 0, 255), thickness=4)

            log.visual(VisualRecord("Match", [img_final], fmt="png"))

            return center_loc, res, screenshot
        else:
            log.debug("Image not matched.")
            return None

    def hover(self, dest, threshold=0.7, update=True):
        if type(dest) == str:
            match_res = self.match(dest, threshold, update)
            if match_res != 0:
                location = match_res[0]
            else:
                location = 0
        elif type(dest) == tuple:
            location = dest
        else:
            log.error("Wrong input type: " + str(type(dest)))
            raise TypeError()

        if location != 0:
            pyag.moveTo(location)
            return 1
        else:
            return 0

    def click(self, dest, threshold=0.7, button='left', update=True):
        log.debug("Click destination is " + str(dest))
        if dest is None:
            pyag.click(button=button)
        elif self.hover(dest, threshold, update):
            pyag.click(button=button)
        else:
            return 0

    def exists(self, image, seconds=2, threshold=0.7):
        check_number = 1
        log.debug("Exists started.")
        while True:
            log.debug("Image " + str(image) + " matching nr " + str(check_number))
            match_time_start = datetime.datetime.now()
            if self.match(image, threshold) is not None:
                return 1
            else:
                match_time_stop = datetime.datetime.now()
                matchingtime = match_time_stop - match_time_start
                matchtime = matchingtime.microseconds / 1000000
                log.debug("Matching time: " + str(matchtime))
                if MATCH_INTERVAL > matchtime:
                    sleep(MATCH_INTERVAL - matchtime)
                    seconds -= MATCH_INTERVAL
                else:
                    seconds -= matchtime
            if seconds <= 0:
                log.debug("Image do not exists.")
                return 0
            check_number += 1

    @staticmethod
    def draw_location(image, location, size, color=(255, 0, 0)):
        top_left = location
        bottom_right = (location[0] + size[1], location[1] + size[0])
        return cv.rectangle(image, top_left, bottom_right, color=color, thickness=2, lineType=cv.LINE_4)

    def find(self, image, threshold=0.7):
        best_location, result, screenshot = self.match(image, threshold)
        locations = np.where(result >= threshold)
        locations = list(zip(*locations[::-1]))
        log.debug("Locations: " + str(locations))

        img = cv.imread(image, cv.IMREAD_UNCHANGED)
        image_size_w, image_size_h, image_size_c = img.shape

        # Draw best location
        for location in locations:
            self.draw_location(screenshot, location, (image_size_w, image_size_h))

    def get_colored_mask(self, colors, mask_filter=False):
        masks_list = []
        for mask_color in colors:
            mask_array = np.array(mask_color, dtype="uint8")
            new_mask = cv.inRange(self.screen, mask_array, mask_array)
            masks_list.append(new_mask)

        final_mask = masks_list[0]
        for mask in masks_list:
            final_mask = final_mask | mask

        output = cv.bitwise_and(self.screen, self.screen, mask=final_mask)

        # convert the image to grayscale
        gray_image = cv.cvtColor(output, cv.COLOR_BGR2GRAY)
        if mask_filter:
            kernel = np.ones((2, 2), np.uint8)
            gray_image = cv.morphologyEx(gray_image, cv.MORPH_OPEN, kernel)
        return gray_image

    def get_color_range_mask(self, color, color2=None, mask_filter=False):
        mask_array = np.array(color, dtype="uint8")
        if color2 is not None:
            mask_array2 = np.array(color2, dtype="uint8")
        else:
            mask_array2 = np.array(color, dtype="uint8")
        mask = cv.inRange(self.screen, mask_array, mask_array2)
        filtered_map = cv.bitwise_and(self.screen, self.screen, mask=mask)

        # convert the image to grayscale
        gray_image = cv.cvtColor(filtered_map, cv.COLOR_BGR2GRAY)
        if mask_filter:
            kernel = np.ones((3, 3), np.uint8)
            gray_image = cv.morphologyEx(gray_image, cv.MORPH_OPEN, kernel)
        return gray_image

    # Find center location of rgb color on screen
    def match_color(self, colors, mask_filter=False, method="contours"):
        if self.screen is None:
            self.update_screen()

        log.debug("Matching color {} with method {}".format(colors, method))

        if method == "contours":
            masked_screen = self.get_colored_mask(colors, mask_filter)
            thresh = cv.threshold(masked_screen, 5, 255, cv.THRESH_BINARY)[1]
            cnts = cv.findContours(thresh.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)

            if not cnts:
                log.debug("Color not found.")
                return None

            c = max(cnts, key=cv.contourArea)

            color_x, color_y = tuple(c[c[:, :, 1].argmax()][0])
        elif method == "nonzero":
            if len(colors) < 2:
                color1 = color2 = colors[0]
            else:
                color1, color2 = colors[0], colors[1]
            masked_screen = self.get_color_range_mask(color1, color2, mask_filter)
            log.debug(VisualRecord("Masked screen", [masked_screen], fmt="png"))
            nonzero_points = cv.findNonZero(masked_screen)
            if nonzero_points is None:
                return None
            color_x, color_y = tuple(nonzero_points[round(len(nonzero_points) / 2)][0])
        else:
            raise TypeError("Unknown match_color method.")

        color_location = color_x + self.x, color_y + self.y

        log.debug("Location found: " + str(color_location))
        return color_location

    def image_mask(self, image, inverted=False):
        log.debug("Image mask start.")
        best_location, result, screenshot = self.match(image)
        locations = np.where(result >= 0.7)
        locations = list(zip(*locations[::-1]))

        img = cv.imread(image, cv.IMREAD_UNCHANGED)
        image_size_w, image_size_h, image_size_c = img.shape
        size = (image_size_w, image_size_h)

        # Draw best location
        for location in locations:
            top_left = location
            bottom_right = (location[0] + size[1], location[1] + size[0])
            cv.rectangle(screenshot, top_left, bottom_right, color=(255, 255, 255), thickness=-1, )

        src_gray = cv.cvtColor(screenshot, cv.COLOR_BGR2GRAY)
        src_gray = cv.blur(src_gray, (5, 5))
        thresh = cv.threshold(src_gray, 150, 255, cv.THRESH_BINARY)[1]
        thresh = cv.erode(thresh, None, iterations=3)
        final = cv.dilate(thresh, None, iterations=3)
        if inverted:
            final = cv.bitwise_not(final)

        return final


def main():
    log.info("pysikuli test")
    win_tooltip = Region(0, 1401, 773, 39)
    if win_tooltip.exists("images_test/win.png"):
        win_tooltip.click("images_test/win.png")
    win_tooltip.hover((10, 10))
    pyag.press("Esc")
    white_location = win_tooltip.match_color([255, 255, 255], method="nonzero")
    win_tooltip.hover(white_location)
    log.info("White color location: " + str(white_location))


def match_test():
    log.info("Match test")
    sleep(2)
    matcher = Region()
    matcher.match("images/malah_destination.png")


if __name__ == '__main__':
    #main()
    match_test()
