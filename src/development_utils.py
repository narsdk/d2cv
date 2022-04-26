from logger import log, GameError
from pysikuli import Region
from src.config import CONFIG
from time import sleep
import datetime
import cv2 as cv
import imutils
import random
import pyautogui as pyag


def get_pixels(image):
    img = cv.imread(image, cv.IMREAD_UNCHANGED)
    #img = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    img = [item for sublist in img.tolist() for item in sublist]
    print(img)
    result_s = []
    result_b = []
    for x in range(0,3):
        smallest = [1000,1000,1000]
        biggest = [0,0,0]
        print("Run for " + str(x))
        for i in img:
            if i[x] < smallest[x]:
                smallest = i
            if i[x] > biggest[x]:
                biggest = i
        print("s:{} b:{}".format(smallest,biggest))
        result_s.append(smallest[x])
        result_b.append(biggest[x])

    print("Result: " + str(result_s) + str(result_b))


def main():
    log.info("Development utils test")
    image = "images/pindle_entrance_colors.png"
    get_pixels(image)


if __name__ == '__main__':
    main()
