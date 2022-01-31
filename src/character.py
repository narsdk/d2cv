from logger import log, GameError
from maptraveler import MapTraveler
from pysikuli import Region
from src.config import CONFIG
import pyautogui as pyag
from time import sleep
import random


class Character:
    def __init__(self, maptraveler):
        self.maptraveler = maptraveler
        self.matcher = Region()

    def teleport_to(self, direction, distance, sleep_time=0.25, offset=None, mode="normal"):
        log.debug("Teleport start")
        direction_location_x, direction_location_y = MapTraveler.MOVE_DIRECTIONS[direction]
        center_x, center_y = CONFIG["CENTER_LOCATION"]

        if offset is not None:
            direction_location_x, direction_location_y = direction_location_x + offset[0], \
                                                         direction_location_y + offset[1]
        teleport_location = MapTraveler.get_move_location(direction_location_x - center_x,
                                                          direction_location_y - center_y, (distance, distance))

        log.debug("Teleport location: " + str(teleport_location))
        if mode == "normal":
            self.matcher.click(teleport_location, button="right")
        elif mode == "continuous":
            pyag.moveTo(teleport_location)
            pyag.mouseDown(button='right')
        sleep(sleep_time)
        if mode == "continuous":
            pyag.mouseUp(button='right')
        log.debug("Teleport end")

    def go_to_destination(self, destination, shift=None, move_step=(250, 350), accepted_distance=20, steps_timeout=30,
                          critical=True, map_filter=False, button="left", move_sleep=0):
        step = 0
        error_counter = 0
        log.info("Going to destination " + str(destination))
        while True:
            step += 1
            log.debug("Started moving loop nr " + str(step))
            if step > steps_timeout:
                log.error("Timeout when going to " + str(destination))
                if critical:
                    raise GameError("Timeout when going to " + str(destination))
                else:
                    log.warning("This is not critical.")
                    return False

            # Checking blockers
            if Region(CONFIG["MINIMAP_REGION"]).exists("images/waypoint.png", 0.01):
                log.warning("Waypoint image found. Closing it.")
                pyag.press("esc")
            log.debug("waypoint checked.")

            diff_location_x, diff_location_y = self.maptraveler.get_diff_from_destination(destination, shift=shift,
                                                                                          map_filter=map_filter)

            # Error counter is used to do not fail function if we do not detect image in single iteration.
            if diff_location_x is None:
                log.warning("Cannot find destination.")
                sleep(0.2)
                if error_counter == 30:
                    return False
                else:
                    error_counter += 1
                    continue
            error_counter = 0

            if abs(diff_location_x) > accepted_distance or abs(diff_location_y) > accepted_distance:
                move_location = MapTraveler.get_move_location(diff_location_x, diff_location_y, move_step)
                self.matcher.click(move_location, button=button)
                sleep(move_sleep)
            else:
                log.info("Destination reached.")
                return True

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
                diff_location_x, diff_location_y = self.maptraveler.get_diff_from_destination(destination,
                                                                                              shift=dest_shift)
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
                self.matcher.hover(checking_location)
                if self.matcher.exists(hover_image, 0.05):
                    log.info("Found {} on location {}".format(hover_image, checking_location))
                    return True

    def enter_destination(self, destination, hover_image, final_image, dest_shift=None, special_shift=None):
        enter_max_attempts = 5
        enter_timeout = 0
        while True:
            enter_timeout += 1
            # Check if no other npc was clicked not intentionally
            if Region(856, 219, 1268, 673).exists("images/cancel.png", 0.1):
                pyag.press("esc")
            if enter_timeout > enter_max_attempts:
                log.error("Timeout when entering " + str(destination))
                raise GameError("Timeout when entering " + str(destination))
            if self.maptraveler.hover_destination(destination, hover_image, dest_shift, special_shift):
                pyag.click()
                sleep(1)
                if self.matcher.exists(final_image, 5):
                    log.debug("Destination entered correctly.")
                    return True

    def goto_entrance(self):
        log.info("Going to located entrance")
        timeout_counter = 0
        while True:
            char_location = self.maptraveler.get_char_location()

            if timeout_counter > 20:
                log.error("Timeout when going to entrance.")
                return False, None

            # Check entrance position
            entrance_location = self.maptraveler.get_entrance_location()
            if entrance_location is None:
                timeout_counter += 1
                sleep(0.3)
                log.warning("Cannot find entrance location nr " + str(timeout_counter))
                continue

            log.info("Character location: {} Entrance location: {}".format(char_location, entrance_location))

            # Go to entrance possition
            entrance_x, entrance_y = entrance_location
            char_x, char_y = char_location
            if abs(entrance_x - char_x) > 40 or abs(entrance_y - char_y) > 40:
                tele_location = self.maptraveler.get_tele_location(char_location, entrance_location)
                self.maptraveler.click(tele_location, button='right')
                sleep(0.7)
                if timeout_counter > 5:
                    self.matcher.click(random.choice(list(MapTraveler.MOVE_DIRECTIONS.values())), button="right")
                    sleep(1)
            else:
                sleep(1)
                if self.hover_destination(([149, 41, 98], [235, 101, 223]), "images/dur.png"):
                    log.info("Entrance hovered")
                    if self.matcher.exists("images/3.png", threshold=0.9):
                        log.info("Entering entrance")
                        self.matcher.click(None)
                    else:
                        log.warning("Wrong entrance found.")
                        return False, self.maptraveler.get_entrance_image()

                    if Region(2162, 109, 386, 39).exists("images/indurance3.png", 5, threshold=0.9):
                        log.info("Destination entered correctly.")
                        return True, None
                    else:
                        log.info("Failed to enter durance level 3.")
                        return False, None
                else:
                    log.error("Cannot find durance description of entrance")
            timeout_counter += 1


def main():
    log.info("Character test")


if __name__ == '__main__':
    main()
