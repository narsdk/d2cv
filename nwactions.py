from d2sikuli import *
from d2map import *
import pyautogui as pyag
import random
import imutils
import threading
import math
import pytesseract
import re

FISHING_REGION = (795,84,1057,1137)
GREEN_COLOR = [(172,242,1),(174,245,2),(168,236,0),(119,168,2)]
ORANGE_COLOR = [(22,112,235),(28,112,229),(19,95,200),(22,114,240)]

def casting():
    log.info("Casting started")
    casting_timeout = 0
    while True:
        casting_timeout += 1
        if casting_timeout > 5:
            log.error("Failed to cast")
            exit(1)
        pyag.mouseDown()
        sleep(1.9)
        pyag.mouseUp()
        sleep(2)
        if exists("images_nw/rod.png",5):
            log.info("Rod found")
            break
        else:
            log.error("LOG DIDNT FOUND")
            sleep(5)

def wait_for_fish():
    log.info("Wait for fish started.")
    while not exists("images_nw/fish_on_rod.png",0.1):
        pass
    log.info("mouseDown.")
    pyag.mouseDown()
    sleep(0.5)


def spinning_wheel():
    log.info("Spinning wheel started.")
    while exists("images_nw/fishericonUp.png",0.1,threshold=0.77,region=FISHING_REGION) and exists("images_nw/fishericonDown.png",0.1,threshold=0.77,region=FISHING_REGION):
        if get_color_location(GREEN_COLOR,region=FISHING_REGION) != (None,None):
            log.info("mouseDown.")
            pyag.mouseDown()
            sleep(0.01)
        elif get_color_location(ORANGE_COLOR,region=FISHING_REGION) != (None,None):
            log.info("mouseUp.")
            pyag.mouseUp()
            sleep(0.01)
    pyag.mouseUp()
    log.info("Fishing complete.")


sleep(5)

fisher_numer = 0
while True:
    fisher_numer += 1
    # Repair rod
    if fisher_numer % 10 == 0:
        log.info("Repairing rod.")
        pyag.press("tab")
        sleep(2)
        pyag.click((1160,885),button="right")
        sleep(2)
        hover((1278,935))
        sleep(1)
        pyag.click((1278,935))
        sleep(1)
        pyag.press("e")
        sleep(1)
        pyag.press("esc")
        sleep(1)
        pyag.press("f3")
        sleep(2)
    if fisher_numer % 10 == 5:
        pyag.press("space")
        sleep(2)
    log.info("Start Fisher number " + str(fisher_numer))
    casting()
    wait_for_fish()
    spinning_wheel()
    sleep(12)