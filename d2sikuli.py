import cv2 as cv
import numpy as np
from math import floor
import pyautogui as pyag
from time import sleep
import logging as log
import logging.handlers
import sys
import datetime
import os
from vlogging import VisualRecord

pyag.PAUSE = 0.03

### DONE
# Improve RotateExtensionLogs class - add possibility to include file extension to log file name
class RotateExtensionLogs(log.handlers.RotatingFileHandler):
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=False, file_extension=""):
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self.file_extension = file_extension

    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename("%s.%d.%s" % (self.baseFilename, i, self.file_extension))
                dfn = self.rotation_filename("%s.%d.%s" % (self.baseFilename, i + 1, self.file_extension))
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = self.rotation_filename(self.baseFilename + ".1." + self.file_extension)
            if os.path.exists(dfn):
                os.remove(dfn)
            self.rotate(self.baseFilename, dfn)
        if not self.delay:
            self.stream = self._open()


# Add new logging level - visual
visual_level = log.INFO - 1
visual_name = "VISUAL"
visual_method_name = "visual"
def logForLevel(self, message, *args, **kwargs):
    if self.isEnabledFor(visual_level):
        self._log(visual_level, message, args, **kwargs)

def logToRoot(message, *args, **kwargs):
    logging.log(visual_level, message, *args, **kwargs)

log.addLevelName(visual_level, visual_name)
setattr(log, visual_name, visual_level)
setattr(log.getLoggerClass(), visual_method_name, logForLevel)
setattr(log, visual_method_name, logToRoot)


# Set file logger
log_name = 'log/d2cv-log.html'

# Set console logger
should_roll_over = os.path.isfile(log_name)
html_handler = RotateExtensionLogs(log_name, mode='w', backupCount=10, maxBytes=100000, file_extension="html")
if should_roll_over:  # log already exists, roll over!
    html_handler.doRollover()

html_log_format = '[%(asctime)s.%(msecs)03d] [%(levelname)s] %(module)s - %(funcName)s: %(message)s<br>'

log.basicConfig(
    filename=log_name,
    level=log.VISUAL,
    format=html_log_format,
    datefmt='%H:%M:%S',
)

log_format = '[%(asctime)s.%(msecs)03d] [%(levelname)s] %(module)s - %(funcName)s: %(message)s'
console_logging = log.StreamHandler()
console_logging.setLevel(log.INFO)
console_logging.setFormatter(log.Formatter(log_format))
log.getLogger().addHandler(console_logging)


# Constants
MATCH_INTERVAL = 0.01
D2_RESOLUTION = (1068,600)
CURRENT_RESOLUTION = (2560,1440)

# Settings
np.set_printoptions(threshold=sys.maxsize)

### DONE
def match(image, threshold=0.7, own_screenshot=None, region=None):

    log.debug("Matching image " + str(image))

    img = cv.imread(image, cv.IMREAD_UNCHANGED)
    img = cv.cvtColor(img, cv.COLOR_RGB2BGR)

    # Get screenshot
    if own_screenshot is not None:
        screenshot = own_screenshot
        screenshot_clean = own_screenshot
    else:
        screen = pyag.screenshot(region=region)
        screenshot_clean = cv.cvtColor(np.array(screen), cv.COLOR_RGB2BGR)
        screenshot = screenshot_clean.copy()

    #cv.imshow("Match rectangled", screenshot)
    #cv.waitKey()

    res = cv.matchTemplate(img, screenshot, cv.TM_CCOEFF_NORMED)

    #cv.imshow("res", res)
    #cv.waitKey()

    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)
    log.debug("Best match location: " + str(max_loc))
    log.debug("Best match similarity: " + str(max_val))

    if max_val > threshold:
        log.debug("Image matched")

        # Creating rectangle
        top_left = max_loc
        image_h, image_w, image_c = img.shape
        log.debug("Image height: " + str(image_h) + " Image width: " + str(image_w))
        location_x, location_y = top_left
        bottom_right = (location_x + image_w, location_y + image_h)
        img_rectangled = cv.rectangle(screenshot,top_left, bottom_right, color=(0, 255, 0), thickness=2, lineType=cv.LINE_4)

        # Creating center point
        center_x = location_x + floor(image_w / 2)
        center_y = location_y + floor(image_h / 2)
        center_loc = (center_x, center_y)
        img_final = cv.circle(img_rectangled, center_loc, radius=0, color=(0, 0, 255), thickness=4)

        # Show image
        #cv.imshow("Match rectangled", img_final)
        #cv.waitKey()
        return center_loc, res, screenshot_clean
    else:
        log.debug("Image not matched.")
        return None,None

### ABADONED
def convert_location(loc):
    game_w, game_h = D2_RESOLUTION
    real_w, real_h = CURRENT_RESOLUTION
    loc_x, loc_y = loc
    return loc_x * (game_w/real_w), loc_y * (game_h/real_h)

### DONE
def hover(input, convert = False, threshold=0.7,region=None):
    if type(input) == str:
        match_res = match(input, threshold, region=region)
        if match_res != 0:
            location = match(input, threshold, region=region)[0]
        else:
            location = 0
    elif type(input) == tuple:
        location = input
    else:
        log.error("Wrong input type: " + str(type(input)))
        return 1

    if region is not None:
        region_x, region_y,_,_ = region
        location_x, location_y = location
        location = (region_x + location_x,region_y + location_y)

    if location != 0:
        if convert:
            location = convert_location(location)
        pyag.moveTo(location)
        return 1
    else:
        return 0

### DONE
def click(input, threshold=0.7, convert=False, button='left', region=None):
    if type(input) == str:
        match_res = match(input, threshold, region=region)
        if match_res != 0:
            location = match_res[0]
        else:
            location = 0
    elif type(input) == tuple:
        location = input
    else:
        log.error("Wrong input type: " + str(type(input)))
        return 1

    if region is not None:
        location_x, location_y = location
        region_x, region_y,_,_ = region
        location = location_x + region_x, location_y + region_y

    if location != None:
        if convert:
            location = convert_location(location)
        log.debug("Clicking location " + str(location))
        pyag.moveTo(location)
        pyag.click(button=button)
        #pyag.moveTo(1,400)
        return 1
    else:
        log.debug("Failed to find " + str(input))
        return 0

### DONE
def exists(image, seconds=2, threshold=0.7, region=None):
    check_number = 1
    log.debug("Exists started.")
    while True:
        log.debug("Image " + str(image) + " matching nr " + str(check_number))
        match_time_start = datetime.datetime.now()
        if match(image, threshold, region=region)[0] is not None:
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

### DONE
def draw_location(image, location, size, color):
    top_left = location
    bottom_right = (location[0] + size[1], location[1] + size[0])
    return cv.rectangle(image, top_left, bottom_right, color=color, thickness=2, lineType=cv.LINE_4)


### DONE
def find(image,threshold = 0.7,region=None):
    best_location, result, screenshot = match(image, threshold, region=region)
    locations = np.where(result >= threshold)
    locations = list(zip(*locations[::-1]))
    log.debug("Locations: " + str(locations))

    img = cv.imread(image, cv.IMREAD_UNCHANGED)
    image_size_w, image_size_h, image_size_c = img.shape

    # Draw best location
    for location in locations:
        draw_location(screenshot, location, (image_size_w, image_size_h))

    # cv.imshow("result", result)
    # cv.waitKey()
    # cv.imshow("All locations", screenshot)
    # cv.waitKey()
    # cv.destroyAllWindows()

#################### DIABLO 2 ACTIONS ####################


### ABADONED
def get_distance(direction,distance):
    res_w, res_h = CURRENT_RESOLUTION
    center_w, center_h = res_w/2, res_h/2
    step_w, step_h = res_w/8, res_h/8

    if direction == "left":
        dir_w = center_w - step_w * distance
        dir_h = center_h
    elif direction == "right":
        dir_w = center_w + step_w * distance
        dir_h = center_h
    elif direction == "down":
        dir_w = center_w
        dir_h = center_h + step_h * distance
    elif direction == "top":
        dir_w = center_w
        dir_h = center_h - step_h * distance
    else:
        log.error("Wrong direction: " + direction)
        return 0
    return dir_w, dir_h