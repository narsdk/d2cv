from logger import log, GameError
from pysikuli import Region
import cv2 as cv
import numpy as np
from vlogging import VisualRecord
import math
import ctypes
from time import sleep
import random
from src.config import CONFIG

MOVE_DIRECTIONS = {
    "t": (1300, 10),
    "d": (1300, 1100),
    "r": (2550, 700),
    "l": (10, 700),
    "tl": (10, 10),
    "tr": (2550, 10),
    "dl": (10, 1400),
    "dr": (2550, 1400)
}

DIRECTION_NUMBERS = ["tl", "tr", "dr", "dl"]

user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


class MapTraveler(Region):
    """
    Class containts all functions responsible for traveling on locations using minimap.
    Making minimap more readable, checking wall possitions and traveling using teleportation algorithms.
    """

    def __init__(self):
        x, y, w, h = CONFIG["MINIMAP_REGION"]
        super().__init__(x, y, w, h)
        self.known_entrance = None
        self.map_walls = None

    # Return image with travel map contours
    def get_map_walls(self, mode="full"):
        if self.screen is None:
            self.update_screen()
        minimap_hsv = cv.cvtColor(self.screen, cv.COLOR_BGR2HSV)

        # walls colors
        lower_map = np.array([0, 16, 27])
        upper_map = np.array([32, 133, 106])

        # other borders colors
        lower_map2 = np.array([0, 0, 44])
        upper_map2 = np.array([45, 87, 160])

        kernel = np.ones((3, 3), np.uint8)
        kernel2 = np.ones((1, 2), np.uint8)

        minimap_mask = cv.inRange(minimap_hsv, lower_map, upper_map)
        minimap_mask2 = cv.inRange(minimap_hsv, lower_map2, upper_map2)

        minimap_mask = cv.morphologyEx(minimap_mask, cv.MORPH_OPEN, kernel)
        minimap_mask2 = cv.morphologyEx(minimap_mask2, cv.MORPH_OPEN, kernel2)

        if mode == "full":
            full_mask = cv.bitwise_or(minimap_mask, minimap_mask2)
        elif mode == "walls":
            full_mask = minimap_mask
        elif mode == "shore":
            full_mask = minimap_mask2
        else:
            raise TypeError("Wrong meph map mode")

        # Hide merc
        merc_rectangle = np.array([[[30, 0], [111, 0], [111, 92], [30, 92]]], dtype=np.int32)
        cv.fillPoly(full_mask, merc_rectangle, (0, 0, 0))

        target = cv.bitwise_and(self.screen, self.screen, mask=full_mask)
        log.visual(VisualRecord("Full mask/target:", [full_mask, target], fmt="png"))
        self.map_walls = full_mask
        return full_mask, target

    # Return entrance location in travel map or None if there are no entrance or entrance is on list
    # of known entrances.
    def get_entrance_location(self):
        log.debug("Checking entrance")
        result = self.match_color([[149, 41, 98], [235, 101, 223]], mask_filter=True)

        if self.known_entrance is not None and result is not None:
            new_entrance = self.get_entrance_image()
            if new_entrance.shape != self.known_entrance.shape:
                return None
            entrance_diff_image = cv.bitwise_and(new_entrance, cv.bitwise_not(self.known_entrance))
            entrance_diff = cv.findNonZero(entrance_diff_image)
            if entrance_diff is None:
                entrance_diff = 0
            else:
                entrance_diff = len(entrance_diff)
            log.visual(
                VisualRecord(("Entrance difference is: {}".format(entrance_diff)), [result, self.known_entrance],
                             fmt="png"))
            if entrance_diff < 800:
                return None

        return result

    def get_entrance_image(self):
        entrance_location = self.get_entrance_location()
        entrance_image = self.map_walls[entrance_location[1] - 80:entrance_location[1] + 80,
                         entrance_location[0] - 80:entrance_location[0] + 80]
        return entrance_image

    @staticmethod
    def get_longest_line(image):
        lines = cv.HoughLinesP(image, 1, np.pi / 180, 10, None, 10, 10)

        if lines is not None:
            longest_line = None
            longest_line_size = 0
            for i in range(0, len(lines)):
                line = lines[i][0]
                line_size = math.sqrt((((line[0] - line[2]) ** 2) + ((line[1] - line[3]) ** 2)))
                if line_size > longest_line_size:
                    longest_line_size = line_size
                    longest_line = line
        else:
            log.error("Cannot find longest line")
            longest_line = None
            longest_line_size = None
        return longest_line, longest_line_size

    def get_start_direction(self):
        map_canny = cv.Canny(self.screen, 50, 200, None, 3)
        char_position = self.get_char_location()

        longest_line, _ = self.get_longest_line(map_canny)
        log.debug("Character location: {} Line parameters: {}. Differences: [{} {} {} {}]".format(char_position,
                                                                                                  longest_line,
                                                                                                  longest_line[0] -
                                                                                                  char_position[0],
                                                                                                  longest_line[1] -
                                                                                                  char_position[1],
                                                                                                  longest_line[2] -
                                                                                                  char_position[0],
                                                                                                  longest_line[3] -
                                                                                                  char_position[1]))

        line_x1, line_y1, line_x2, line_y2 = longest_line
        line_x1 = line_x1 - char_position[0]
        line_x2 = line_x2 - char_position[0]
        line_y1 = line_y1 - char_position[1]
        line_y2 = line_y2 - char_position[1]

        # Checking values for right
        if -10 < line_x1 < 60 and \
                20 < line_y1 < 60 and \
                120 < line_x2 < 190 and \
                -40 < line_y2 < 0:
            result = "tr"

        # Checking values for top
        elif -150 < line_x1 < -30 and \
                -30 < line_y1 < 30 and \
                0 < line_x2 < 60 and \
                30 < line_y2 < 100:
            result = "tl"

        # Checking values for left
        elif -50 < line_x1 < 0 and \
                30 < line_y1 < 120 and \
                30 < line_x2 < 120 and \
                -20 < line_y2 < 30:
            result = "dl"

        # Checking values for down
        elif -130 < line_x1 < -20 and \
                -30 < line_y1 < 30 and \
                -20 < line_x2 < 80 and \
                40 < line_y2 < 150:
            result = "dr"

        else:
            log.warning("Didnt found best direction for meph route.")
            result = "tl"

        return result

    @staticmethod
    def direction_resolver(direction, resolution):
        resolution_x, resolution_y = resolution
        move_directions = {
            "t": (int(resolution_x / 2), 0),
            "d": (int(resolution_x / 2), resolution_y),
            "r": (resolution_x, int(resolution_y / 2)),
            "l": (0, int(resolution_y / 2)),
            "tl": (0, 0),
            "tr": (resolution_x, 0),
            "dl": (0, resolution_y),
            "dr": (resolution_x, resolution_y),
            "c": (int(resolution_x / 2), int(resolution_y / 2))
        }
        return move_directions[direction]

    # TODO: Used to teleport to entrance on travel maps, should be replaced by go_to_destination
    @staticmethod
    def get_tele_location(current_loc, destination_loc):
        current_x, current_y = current_loc
        destination_x, destination_y = destination_loc
        # top
        if (abs(current_x - destination_x) <= 40) and (current_y - destination_y >= 30):
            tele_loc = MOVE_DIRECTIONS["t"]
        # down
        elif (abs(current_x - destination_x) <= 40) and (current_y - destination_y <= -30):
            tele_loc = MOVE_DIRECTIONS["d"]
        # right
        elif (current_x - destination_x <= -40) and (abs(current_y - destination_y) <= 30):
            tele_loc = MOVE_DIRECTIONS["r"]
        # left
        elif (current_x - destination_x >= 40) and (abs(current_y - destination_y) <= 30):
            tele_loc = MOVE_DIRECTIONS["l"]
        # top left
        elif (current_x - destination_x >= 40) and (current_y - destination_y >= 30):
            tele_loc = MOVE_DIRECTIONS["tl"]
        # top right
        elif (current_x - destination_x <= -40) and (current_y - destination_y >= 30):
            tele_loc = MOVE_DIRECTIONS["tr"]
        # down left
        elif (current_x - destination_x >= 40) and (current_y - destination_y <= -30):
            tele_loc = MOVE_DIRECTIONS["dl"]
        # down right
        elif (current_x - destination_x <= -40) and (current_y - destination_y <= -30):
            tele_loc = MOVE_DIRECTIONS["dr"]
        else:
            log.error("Unknown tele_loc")
            tele_loc = None

        return tele_loc

    # TODO: Do we need to check it? maybe its constans?
    def get_char_location(self):
        char_location = (None, None)
        fail_counter = 0
        while char_location == (None, None):
            char_location = self.match_color([159, 85, 21], [253, 136, 43])
            if char_location == (None, None):
                # If character counter on minimap is under some text then color is different
                char_location = self.match_color([193, 104, 25], [253, 136, 33])
                if char_location == (None, None):
                    log.warning("Failed to find character.")
                    fail_counter += 1
                    sleep(0.1)
                    if fail_counter > 5:
                        return 433, 248
        return char_location

    # return vector of distance of character from destination point on minimap
    # destination can be an image patch or colors range in touple
    def get_diff_from_destination(self, destination, shift=None, map_filter=False):
        log.debug("Starting get_diff_from_destination")

        char_location = self.get_char_location()

        if type(destination) == str:
            destination_location, *rest = self.match(destination)
        else:
            destination_color1, destination_color2 = destination
            destination_location = self.match_color([destination_color1, destination_color2], map_filter)

        if destination_location is None:
            log.warning("Failed to find destination.")
            return None

        char_location_x, char_location_y = char_location
        destination_location_x, destination_location_y = destination_location
        if shift is not None:
            shift_x, shift_y = shift
            destination_location_x = destination_location_x + shift_x
            destination_location_y = destination_location_y + shift_y

        diff_location_x = destination_location_x - char_location_x
        diff_location_y = destination_location_y - char_location_y

        log.debug("Char location: {} Destination location: {} Diff location: {},{}".format(char_location,
                                                                                           destination_location,
                                                                                           diff_location_x,
                                                                                           diff_location_y))

        return diff_location_x, diff_location_y

    def hover_destination(self, destination, hover_image, dest_shift=None, special_shift=None):
        hover_destination_timeout = 0
        while True:
            log.info("hover_destination nr " + str(hover_destination_timeout))
            hover_destination_timeout += 1
            if hover_destination_timeout > 5:
                log.error("Failed to find " + str(hover_image))
                return False
            find_map_destination_timeout = 0
            while True:
                find_map_destination_timeout += 1
                if find_map_destination_timeout > 20:
                    log.error("Timeout when hovering destination" + str(destination))
                    raise GameError("Timeout when hovering destination" + str(destination))

                log.debug("Trying to find location nr " + str(find_map_destination_timeout))
                diff_location_x, diff_location_y = self.get_diff_from_destination(destination, shift=dest_shift)
                if diff_location_x is not None and diff_location_y is not None:
                    break

            center_x, center_y = CONFIG["CENTER_LOCATION"]

            finding_shifts = [(0, 0), (100, 0), (-100, 0), (0, 100), (0, -100), (100, 100), (100, -100), (-100, 100),
                              (-100, -100),
                              (200, 0), (-200, 0), (0, 200), (0, -200), (200, 200), (200, -200), (-200, 200),
                              (-200, -200),
                              (200, 100), (-200, 100), (100, 200), (100, -200), (200, -100), (-200, -100), (-100, 200),
                              (-100, -200),
                              (0, 250), (250, 0), (-250, 0), (0, -250), (250, 250), (250, -250), (-250, 250),
                              (-250, -250)]

            if special_shift is not None:
                special_shift_x, special_shift_y = special_shift
            else:
                special_shift_x, special_shift_y = (0, 0)

            for shift in finding_shifts:
                shift_x, shift_y = shift
                checking_location = (center_x + (diff_location_x * 15) + shift_x + special_shift_x,
                                     center_y + (diff_location_y * 15) + shift_y + special_shift_y)
                self.hover(checking_location)
                if self.exists(hover_image, 0.05):
                    log.info("Found {} on location {}".format(hover_image, checking_location))
                    return True

    def goto_entrance(self):
        log.info("Going to located entrance")
        timeout_counter = 0
        while True:
            char_location = self.get_char_location()

            if timeout_counter > 20:
                log.error("Timeout when going to entrance.")
                return False, None

            # Check entrance position
            entrance_location = self.get_entrance_location()
            if entrance_location == (None, None):
                timeout_counter += 1
                sleep(0.3)
                log.warning("Cannot find entrance location nr " + str(timeout_counter))
                continue

            log.info("Character location: {} Entrance location: {}".format(char_location, entrance_location))

            # Go to entrance possition
            entrance_x, entrance_y = entrance_location
            char_x, char_y = char_location
            if abs(entrance_x - char_x) > 40 or abs(entrance_y - char_y) > 40:
                tele_location = self.get_tele_location(char_location, entrance_location)
                self.click(tele_location, button='right')
                sleep(0.7)
                if timeout_counter > 5:
                    self.click(random.choice(list(MOVE_DIRECTIONS.values())), button="right")
                    sleep(1)

            # TODO: This part should be moved to tasker
            else:
                sleep(1)
                if self.hover_destination(([149, 41, 98], [235, 101, 223]), "images/dur.png"):
                    log.info("Entrance hovered")
                    if self.exists("images/3.png", threshold=0.9):
                        log.info("Entering entrance")
                        self.click()
                    else:
                        log.warning("Wrong entrance found.")
                        return False, self.get_entrance_image()

                    if self.exists("images/indurance3.png", 5, region=(2162, 109, 386, 39), threshold=0.9):
                        log.info("Destination entered correctly.")
                        return True, None
                    else:
                        log.info("Failed to enter durance level 3.")
                        return False, None
                else:
                    log.error("Cannot find durance description of entrance")
            timeout_counter += 1

    def find_line(self, meph_map, direction="tl", mask_type="terain"):
        meph_map = cv.cvtColor(meph_map, cv.COLOR_GRAY2BGR)
        map_lined_normal = meph_map.copy()

        map_blured = cv.GaussianBlur(map_lined_normal, (9, 9), 0)

        thresh, map_blured = cv.threshold(map_blured, 50, 255, cv.THRESH_BINARY)
        map_blured_gray = cv.cvtColor(map_blured, cv.COLOR_BGR2GRAY)

        cnts, hierarchy = cv.findContours(map_blured_gray.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        list_of_pts = []
        for ctr in cnts:
            list_of_pts += [pt[0] for pt in ctr]

        map_mask = np.zeros((map_blured_gray.shape[0], map_blured_gray.shape[1]), np.uint8)
        if mask_type == "terain":
            mask_direction_poly = {
                "tl": np.array([[(15, 65), (40, 45), (80, 65), (55, 85)]]),  # done
                "tr": np.array([[(15, 70), (40, 90), (80, 60), (55, 40)]]),  # done
                "dl": np.array([[(50, 00), (80, 30), (40, 50), (10, 20)]]),  # done
                "dr": np.array([[(40, 10), (15, 30), (55, 60), (80, 40)]])  # done
            }
        elif mask_type == "wall":
            mask_direction_poly = {
                "tl": np.array([[(100, 80), (70, 100), (100, 100)]]),  # done
                "tr": np.array([[(0, 80), (30, 100), (0, 100)]]),  # done
                "dl": np.array([[(70, 0), (100, 20), (100, 0)]]),  # done
                "dr": np.array([[(0, 0), (0, 20), (30, 0)]])  # done
            }
        else:
            log.error("Unknown mask_type")
            raise TypeError("Unknown mask_type")
        map_mask = cv.fillPoly(map_mask, pts=[mask_direction_poly[direction]], color=(255, 255, 255))

        masked_mask = cv.bitwise_and(map_blured_gray, map_mask)

        _, longest_line_size = self.get_longest_line(masked_mask)

        log.debug("Longest line size on map is " + str(longest_line_size))

        return map_lined_normal, longest_line_size


def main():
    log.info("Mapper test")
    # Go near


if __name__ == '__main__':
    main()
