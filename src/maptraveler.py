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

DIRECTION_NUMBERS = ["tl", "tr", "dr", "dl"]

user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


class MapTraveler(Region):
    """
    Class containts all functions responsible for traveling on locations using minimap.
    Making minimap more readable, checking wall possitions and traveling using teleportation algorithms.
    """

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

    def __init__(self):
        x, y, w, h = CONFIG["MINIMAP_REGION"]
        super().__init__(x, y, w, h)
        self.known_entrance = None
        self.screen_transformed = None
        self.previous_screen_transformed = None

    # Return image with travel map contours
    def get_map_walls(self, mode="full"):
        log.debug("get_map_walls start")
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
        self.previous_screen_transformed = self.screen_transformed
        self.screen_transformed = full_mask
        log.debug("get_map_walls end")
        return full_mask, target

    # Return entrance location in travel map or None if there are no entrance or entrance is on list
    # of known entrances.
    def get_entrance_location(self):
        log.debug("Checking entrance")
        result = self.match_color([[149, 41, 98], [235, 101, 223]], method="nonzero", mask_filter=True)

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
        entrance_image = self.screen_transformed[entrance_location[1] - 80:entrance_location[1] + 80,
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
            longest_line_size = 0
        return longest_line, longest_line_size

    def get_start_direction(self):
        shore_map, _ = self.get_map_walls(mode="shore")
        map_canny = cv.Canny(shore_map, 50, 200, None, 3)
        char_position = self.get_char_location()

        longest_line, _ = self.get_longest_line(map_canny)
        log.debug("Character location: {} Line parameters: {}. Differences: [{} {} {} {}]".format(char_position,
                    longest_line, longest_line[0] - char_position[0], longest_line[1] - char_position[1],
                    longest_line[2] - char_position[0], longest_line[3] - char_position[1]))

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
            tele_loc = MapTraveler.MOVE_DIRECTIONS["t"]
        # down
        elif (abs(current_x - destination_x) <= 40) and (current_y - destination_y <= -30):
            tele_loc = MapTraveler.MOVE_DIRECTIONS["d"]
        # right
        elif (current_x - destination_x <= -40) and (abs(current_y - destination_y) <= 30):
            tele_loc = MapTraveler.MOVE_DIRECTIONS["r"]
        # left
        elif (current_x - destination_x >= 40) and (abs(current_y - destination_y) <= 30):
            tele_loc = MapTraveler.MOVE_DIRECTIONS["l"]
        # top left
        elif (current_x - destination_x >= 40) and (current_y - destination_y >= 30):
            tele_loc = MapTraveler.MOVE_DIRECTIONS["tl"]
        # top right
        elif (current_x - destination_x <= -40) and (current_y - destination_y >= 30):
            tele_loc = MapTraveler.MOVE_DIRECTIONS["tr"]
        # down left
        elif (current_x - destination_x >= 40) and (current_y - destination_y <= -30):
            tele_loc = MapTraveler.MOVE_DIRECTIONS["dl"]
        # down right
        elif (current_x - destination_x <= -40) and (current_y - destination_y <= -30):
            tele_loc = MapTraveler.MOVE_DIRECTIONS["dr"]
        else:
            log.error("Unknown tele_loc")
            tele_loc = None

        return tele_loc

    # TODO: Do we need to check it? maybe its constans?
    def get_char_location(self):
        char_location = None
        fail_counter = 0
        while char_location is None:
            char_location = self.match_color([[95, 51, 12], [253, 136, 39]], method="nonzero")
            if char_location is None:
                # If character counter on minimap is under some text then color is different
                char_location = self.match_color([[193, 104, 25], [253, 136, 33]], method="nonzero")
                if char_location is None:
                    log.warning("Failed to find character.")
                    fail_counter += 1
                    sleep(0.1)
                    if fail_counter > 5:
                        return 433, 248
        log.debug("Character location is " + str(char_location))
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
            destination_location = self.match_color([destination_color1, destination_color2], map_filter,
                                                    method="nonzero",)

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
        log.visual(
            VisualRecord("Longest line: {}".format(longest_line_size), [masked_mask], fmt="png"))
        return map_lined_normal, longest_line_size

    @staticmethod
    def get_move_location(diff_location_x, diff_location_y, distance_step):
        distance_min, distance_max = distance_step
        log.debug(
            "Calculating move location from diff_location_x:{}, diff_location_y:{}, distance_min:{},"
            "distance_max:{}".format(diff_location_x, diff_location_y, distance_min, distance_max))
        random_distance = random.randint(distance_min, distance_max)
        center_x, center_y = CONFIG["CENTER_LOCATION"]

        # New calculations
        current_length = math.sqrt((diff_location_x ** 2) + (diff_location_y ** 2))
        distance_factor = random_distance / current_length
        result_x = int(center_x + (diff_location_x * distance_factor))
        result_y = int(center_y + (diff_location_y * distance_factor))

        log.debug("Move location result: ({},{})".format(result_x, result_y))

        return result_x, result_y

    def check_direction(self, current_direction, turn=None, mask_type="terain"):
        minimap = self.screen_transformed
        map_slicer = {
            "tl": minimap[148:248, 336:436],
            "tr": minimap[152:252, 430:530],
            "dr": minimap[240:340, 430:530],
            "dl": minimap[242:342, 338:438]
        }

        if turn == "left":
            screen_direction = DIRECTION_NUMBERS[(DIRECTION_NUMBERS.index(current_direction) - 1) % 4]
        elif turn == "right":
            screen_direction = DIRECTION_NUMBERS[(DIRECTION_NUMBERS.index(current_direction) - 1) % 4]
        else:
            screen_direction = current_direction
        log.debug("Checking screen from direction {} and mask_type {}".format(screen_direction, mask_type))
        map_part = map_slicer[screen_direction]

        test_scr, line_size = self.find_line(map_part, screen_direction, mask_type)
        log.visual(
            VisualRecord(("Checking direction: {} turn: {}".format(current_direction, turn)), [test_scr], fmt="png"))

        if line_size > 0:
            return True
        else:
            return False

    def find_new_direction(self, current_direction, last_moves):
        # Define main factors - character blocked comparing to last move, wall on forward and wall on left
        # (no new terrain to go)
        character_blocked = self.compare_screens(self.screen_transformed, self.previous_screen_transformed) < 1000
        forward_terrain = self.check_direction(current_direction)
        forward_wall = self.check_direction(current_direction, mask_type="wall")
        left_terrain = self.check_direction(current_direction, turn="left")
        left_wall = self.check_direction(current_direction, turn="left", mask_type="wall")

        turned_right = turned_left = False

        if forward_wall and not forward_terrain and left_wall and not left_terrain and character_blocked:
            direction_result = DIRECTION_NUMBERS[(DIRECTION_NUMBERS.index(current_direction) + 1) % 4]
            turned_right = True
        elif character_blocked and len(last_moves) > 0 and last_moves[-1][3] and not last_moves[-1][1]:
            direction_result = DIRECTION_NUMBERS[(DIRECTION_NUMBERS.index(current_direction) + 1) % 4]
            turned_right = True
        elif left_terrain and sum(map(lambda x: x[2] is True, last_moves[-2:])) == 0 and sum(
                map(lambda x: x[4] is True, last_moves[-5:])) < 5:
            direction_result = DIRECTION_NUMBERS[(DIRECTION_NUMBERS.index(current_direction) - 1) % 4]
            turned_left = True
        else:
            direction_result = current_direction

        last_moves.append((direction_result, turned_right, turned_left, character_blocked, left_terrain))
        return direction_result, last_moves


def main():
    log.info("Mapper test")
    sleep(2)
    traveler = MapTraveler()
    traveler.update_screen()
    match_res = traveler.match_color([[149, 41, 98], [235, 101, 223]], method="nonzero", mask_filter=True)
    log.info("Matching some colors test: " + str(match_res))
    char = traveler.get_char_location()
    log.info("Finding character text: " + str(char))


if __name__ == '__main__':
    main()
