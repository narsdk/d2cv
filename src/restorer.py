from logger import log, GameError
from pysikuli import Region
from src.config import CONFIG
from time import sleep
import datetime
import cv2 as cv
import pyautogui as pyag


class Restorer:
    def __init__(self):
        self.screen = Region()

    # Restore game after crash



def main():
    log.info("Restorer test.")
    sleep(2)
    restorer = Restorer()
    restorer.game_restore()

if __name__ == '__main__':
    main()
