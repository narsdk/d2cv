from logger import log
from pysikuli import Region
import cv2 as cv
import numpy as np
from vlogging import VisualRecord

MINIMAP_REGION = (0, 50, 860, 485)


class MapTraveler(Region):
    """
    Class containts all functions responsible for traveling on locations using minimap.
    Making minimap more readable, checking wall possitions and traveling using teleportation algorithms.
    """
    def __init__(self):
        x, y, w, h = MINIMAP_REGION
        super().__init__(x, y, w, h)
        self.known_entrance = None
        self.map_walls = None

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
        entrance_image = self.map_walls[entrance_location[1]-80:entrance_location[1]+80,
                                         entrance_location[0]-80:entrance_location[0]+80]
        return entrance_image

    def get_start_direction(map, minimap):
        map_canny = cv.Canny(map, 50, 200, None, 3)

        char_possition = get_char_location(minimap)

        # Copy edges to the images that will display the results in BGR
        cdstP = cv.cvtColor(map_canny, cv.COLOR_GRAY2BGR)

        linesP = cv.HoughLinesP(map_canny, 1, np.pi / 180, 10, None, 20, 10)

        if linesP is not None:
            cv.circle(cdstP, char_possition, 5, color=(255, 0, 0),thickness=5)
            longest_line_size = 0
            for i in range(0, len(linesP)):
                l = linesP[i][0]
                #cv.line(cdstP, (l[0], l[1]), (l[2], l[3]), (0, 0, 255), 3, cv.LINE_AA)
                line_size =  math.sqrt((((l[0] - l[2])**2) + ((l[1] - l[3])**2)))
                if line_size > longest_line_size:
                    longest_line_size = line_size
                    longest_line = l
            cv.line(cdstP, (longest_line[0], longest_line[1]), (longest_line[2], longest_line[3]), (0, 0, 255), 3, cv.LINE_AA)
        else:
            log.error("Cannot find longest line")

        log.debug("Character location: {} Line parameters: {}. Differences: [{} {} {} {}]".format(char_possition,longest_line,longest_line[0]-char_possition[0],longest_line[1]-char_possition[1],longest_line[2]-char_possition[0],longest_line[3]-char_possition[1]))

        line_x1, line_y1, line_x2, line_y2 = longest_line
        line_x1 = line_x1 - char_possition[0]
        line_x2 = line_x2 - char_possition[0]
        line_y1 = line_y1 - char_possition[1]
        line_y2 = line_y2 - char_possition[1]

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

        cv.putText(cdstP,result,(400,400),cv.FONT_HERSHEY_SIMPLEX,1,(255, 0, 0),2)
        map = cv.cvtColor(map, cv.COLOR_GRAY2BGR)
        #cv.imshow("Result", np.hstack([minimap, map, cdstP]))
        #cv.waitKey(0)

        return result


def main():
    log.info("Mapper test")


if __name__ == '__main__':
    main()
