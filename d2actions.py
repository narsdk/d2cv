from d2sikuli import *
from d2map import *
import pyautogui as pyag
import random
import imutils
import threading
import math
import pytesseract
import re
from difflib import SequenceMatcher

# Download and install tesseract from https://github.com/UB-Mannheim/tesseract/wiki
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'

pyag.FAILSAFE = False

###### CONFIGURATION

TELEPORT_KEY = "f2"
ATTACK_KEY = "f1"
ATTACK_KEY2 = "f6"
ARMOR_KEY = "f4"
PORTAL_KEY = "f5"

MANA_PERCENT_TO_DRINK_POTION = 10
LIFE_PERCENT_TO_DRINK_POTION = 70
LIFE_PERCENT_TO_DRINK_REJU = 20

USE_MERC = 1
MERC_LIFE_TO_DRINK_POTION = 60

games_max = 10000
difficulty = "hell"


### REGIONS
CENTER_LOCATION = (1280,700)
MINIMAP_REGION = (0,160,672,436)
MERC_REGION = (24,21,95,122)
#POTIONS_BAR_REGION = (1449,1199,325,77) # 3 bar1450,1126,324,74
POTIONS_BAR_REGION = (1450,1122,325,77) # 4 bar
POTIONS_BAR_REGION2 = (1450,1277,325,77)# 2 bar
POTIONS_HEALTH_REGION = (1448,1122,163,79)
POTIONS_MANA_REGION = (1613,1122,161,77)
TRADER_REGION = (0,0,930,1140)

EQUPMENT_REGION = (1691,736,262,263)
EMPTY_GOLD_REGION = (567,1008,20,36)
GOLD_REGION = (419,984,252,75)
CHAR_GOLD_REGION = (1895,1015,250,68)
STASH_BARS_REGION = (212,247,664,53)
STASH_LOCATIONS=[(296,271),(460,271),(626,268),(794,266)]
TV_REGION = (1027,603,507,187)

### COLORS

GREEN_TEXT=[0,255,0]
WHITE_TEXT=[255,255,255]
BLUE_TEXT=[255,104,104]
GOLD_TEXT=[113,175,196]
RED_TEXT=[71,71,255]
ORANGE_TEXT=[0,163,255]

######

class GameError(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)


# Get mana or life amount
def get_resource(resource_type):
    if resource_type == "health":
        region = (500,1205,240,230)
        color1a = (0, 50, 20)
        color1b = (5, 255, 255)
        color2a = (175, 50, 20)
        color2b = (180, 255, 255)
    elif resource_type == "mana":
        region = (1815,1205,240,230)
        color1a = (100, 150, 0)
        color1b = (140, 255, 255)
        color2a = (100, 150, 0)
        color2b = (140, 255, 255)

    resource_bar = get_screen(part=region)
    resource_bar_hsv = cv.cvtColor(resource_bar, cv.COLOR_BGR2HSV)

    ## Gen lower mask (0-5) and upper mask (175-180) of RED
    mask1 = cv.inRange(resource_bar_hsv, color1a, color1b)
    mask2 = cv.inRange(resource_bar_hsv, color2a, color2b)

    ## Merge the mask and crop the red regions
    mask = cv.bitwise_or(mask1, mask2)
    filtered_bar = cv.bitwise_and(resource_bar, resource_bar, mask=mask)

    # convert the image to grayscale
    gray_image = cv.cvtColor(filtered_bar, cv.COLOR_BGR2GRAY)
    gray = cv.GaussianBlur(gray_image, (5, 5), 0)

    # threshold the image, then perform a series of erosions + dilations to remove any small regions of noise
    thresh1 = cv.threshold(gray, 5, 255, cv.THRESH_BINARY)[1]
    thresh2 = cv.erode(thresh1, None, iterations=2)
    thresh = cv.dilate(thresh2, None, iterations=2)

    # find contours in thresholded image, then grab the largest
    # one
    cnts = cv.findContours(thresh.copy(), cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    if not cnts:
        log.warning("Cannot find resource contours.")
        return -1

    c = max(cnts, key=cv.contourArea)

    extTop = tuple(c[c[:, :, 1].argmin()][0])

    log.debug("Top bar value: " + str(extTop))
    _,top_y = extTop

    resource = 100 - (top_y / 2.3)

    log.debug("Resource: " + str(resource_type) + " value is " + str(resource))
    return resource


def get_merc_life():
    merc_screen = get_screen(part=MERC_REGION)
    mask1 = cv.inRange(merc_screen, (0, 126, 0), (0, 126, 0))
    mask2 = cv.inRange(merc_screen, (27, 126, 205), (27, 126, 205))
    mask3 = cv.inRange(merc_screen, (23, 3, 239), (23, 3, 239))

    ## Merge the mask and crop the red regions
    mask = cv.bitwise_or(mask1, mask2, mask3)
    filtered_bar = cv.bitwise_and(merc_screen, merc_screen, mask=mask)

    # convert the image to grayscale
    gray_image = cv.cvtColor(filtered_bar, cv.COLOR_BGR2GRAY)

    # find contours in thresholded image, then grab the largest one
    cnts = cv.findContours(gray_image.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    if not cnts:
        log.warning("Cannot find resource contours.")
        return -1

    c = max(cnts, key=cv.contourArea)

    extRight = tuple(c[c[:, :, 0].argmax()][0])

    right_x, _ = extRight
    merc_life = right_x * 1.16
    log.debug("Merc life: " + str(merc_life))
    return merc_life


# Drink potions when needed, started in thread
def potioner(stop):
    log.info("Start potioner thread.")
    healing_delay = 7 # wait 5 seconds after heal to heal again - workaround to not use all potions too fast
    merc_healed_time = datetime.datetime.now()
    char_healed_time = datetime.datetime.now()
    while True:
        if stop():
            log.info("Finishing potioner.")
            break

        if exists("images/continue.png",0.03,region=(1055,728,452,87)):
            log.error("You are dead!")
            sleep(3)
            click("images/continue.png")
            raise GameError("Hero is dead.")

        if not exists("images/ingame.png", 1):
            log.warning("Cannot find ingame image. Waiting for it.")
            continue

        current_time = datetime.datetime.now()

        if USE_MERC and exists("images/merc_exists.png",0.03,region=MERC_REGION):
            merc_life = get_merc_life()
            merc_heal_time_delay = current_time - merc_healed_time
            if merc_life < MERC_LIFE_TO_DRINK_POTION and merc_heal_time_delay.seconds > healing_delay:
                log.info("Healing merc.")
                with pyag.hold('shift'):
                    pyag.press(str(random.randint(1, 2)))
                merc_healed_time = datetime.datetime.now()

        life_percent = get_resource("health")
        mana_percent = get_resource("mana")

        log.debug("Life: {}% Mana: {}%".format(life_percent,mana_percent))
        if life_percent == -1 or mana_percent == -1:
            log.error("Failed to get resources.")
            continue

        char_heal_time_delay = current_time - char_healed_time
        if life_percent < LIFE_PERCENT_TO_DRINK_POTION and char_heal_time_delay.seconds > healing_delay:
            log.info("Drinking health potion.")
            drink_potion("health")
            char_healed_time = datetime.datetime.now()
        if mana_percent < MANA_PERCENT_TO_DRINK_POTION:
            log.info("Drinking mana potion.")
            drink_potion("mana")


# Dring mana or health potion
def drink_potion(type):
    if type == "health":
        pyag.press(str(random.randint(1,2)))
    elif type == "reju":
        pyag.press("2")
    elif type == "mana":
        pyag.press(str(random.randint(3,4)))

# Random tele or move on lock
def random_on_lock(old_map, new_map,button = "right"):
    map_diff = get_map_difference(old_map, new_map)

    if map_diff < 2500:
        click(random.choice(list(move_directions.values())), button)

def goto_entrance():
    log.info("Going to located entrance")
    timeout_counter = 0
    while True:
        minimap = get_screen(part="minimap")

        old_map = get_easy_map(minimap,char_location)

        if timeout_counter > 10:
            log.error("Timeout when going to entrance.")
            exit(1)

        # Check entrance possition
        entrance_location = get_object_location_by_color(minimap,[161,49,173])
        if entrance_location is None:
            timeout_counter += 1
            sleep(0.3)
            log.warning("Cannot find entrance location nr " + str(timeout_counter))
            continue

        log.info("Character location: {} Entrance location: {}".format(char_location,entrance_location))

        # Go to entrance possition
        entrance_x, entrance_y = entrance_location
        char_x, char_y = char_location
        if abs(entrance_x - char_x) > 40 or abs(entrance_y - char_y) > 30:
            tele_location = get_tele_location(char_location, entrance_location)
            click(tele_location, button='right')
            time.sleep(0.2)
            minimap = get_screen(part="minimap")
            new_map = get_easy_map(minimap, char_location)
            random_on_lock(old_map, new_map)

        # if its close enough then try to find click location
        else:
            search_location = minimap_to_game_location(char_location, entrance_location)
            log.info("search location: " + str(search_location))
            hover(search_location)
            if exists("images/dur.png"):
                log.info("Entrance hovered")
                if exists("images/3.png"):
                    log.info("Entering entrance")
                    click(search_location)
                    exit(0)
                else:
                    log.warning("Wrong entrance found.")
                    exit(1)
            else:
                log.error("Cannot find durance description of entrance")
                exit(1)
        # check if its correct entrance (lvl 3 not 1)
        # if its not correct then mark this part of map as wrong location to be ignored
        # if yes then go in

def goto_wp(point):
    log.info("Going to way point.")
    while not exists("images/wp-active.png"):
        while not exists("images/wp-act1-main.png", 0.1):
            if exists("images/wp-act1-map.png", 0.6):
                click("images/wp-act1-map.png")

        click("images/wp-act1-main.png")
        sleep(2)

        if not exists("images/wp-active.png"):
            click(get_distance("down", 1))

    if exists("images/wp-act1-" + str(point) + ".png"):
        log.info("Selecting location " + point)
        click("images/wp-act1-" + str(point) + ".png")
        return 0
    else:
        log.error("Cannot find point " + point)
        return 1

def teleporter():
    time.sleep(5)
    tele_locations = [(10,10),(2550,10),(2550,1100),(10,1100)]
    tele_nr = 1

    minimap = get_screen(part="minimap")
    char_location_x, char_location_y = get_object_location_by_color(minimap,[254, 148, 55])
    char_location = (char_location_x - 3, char_location_y - 3)
    old_map = get_easy_map(minimap,char_location)


    turn_counter = 0
    block_counter = 0
    side_checker = 0
    while True:
        turn_counter += 1
        log.debug("Start turn nr: " + str(turn_counter))
        # Drink potion every 20 turns
        if turn_counter % 20 == 0:
            drink_potion("mana")
        #Teleport
        click(tele_locations[(tele_nr+(side_checker % 2)) % len(tele_locations)],button='right')
        if side_checker > 0:
            side_checker -= 1

        time.sleep(0.2)

        minimap = get_screen(part="minimap")

        # Checking if entrance was found
        entrance_map = put_mask(minimap,[161,49,173])
        if np.sum(entrance_map) > 0:
            log.debug("Entrance found. np.sum: " + str(np.sum(entrance_map)))
            goto_entrance()
            exit(0)

        new_map = get_easy_map(minimap,char_location)
        old_map = new_map

        map_diff = get_map_difference(old_map,new_map)

        # Change tele location if map diff is small
        if map_diff < 2500:
            if block_counter < 1:
                block_counter += 1
            else:
                #tele_nr = (tele_nr + 1) % len(tele_locations)
                tele_nr = (tele_nr + random.choice([-1,1])) % len(tele_locations)
                log.debug("Chaning tele location to: " + str(tele_locations[tele_nr]))
                block_counter = 0
                side_checker = 3


# Restore game after crash
def game_restore():
    log.info("Game restoring start")
    if not exists("images/play.png", 1):
        restore_timeout = 0
        while True:
            restore_timeout += 1
            if restore_timeout % 5 == 0:
                log.info("Alt+F4 as loading found")
                with pyag.hold('alt'):
                    pyag.press("f4")
                sleep(10)
                pyag.press("up")
                sleep(2)
                pyag.press("enter")
                sleep(10)
            if restore_timeout > 100:
                log.info("Fatal error: cannot find launcher")
                exit(1)
            #launcher = get_color_location([255, 224, 116], region=(438,1399,151,41))
            #if launcher != (None, None):
            log.info("Clicking launcher")
            click((513,1416))
            sleep(2)

            graj = get_color_location([255, 224, 116], region=(342,899,530,396))
            if graj != (None, None):
                log.info("Clicking graj")
                graj_x,graj_y = graj
                graj =  (graj_x - 100, graj_y)
                click(graj, region=(342,899,530,396))
                sleep(2)
                break
            else:
                log.error("Cannot find graj")
                sleep(30)

        while not exists("images/play.png", 10):
            log.info("Waiting for play image.")
            sleep(20)
            pyag.press("space")

        log.info("Restoring game success.")
    else:
        log.info("Play exists?")


# Start game
def start_game():
    log.info("Checking if temviewer message exists.")
    if exists("images/tv.png", 1,threshold=0.65, region=TV_REGION):
        log.info("TV exists. Clicking ok.")
        click((1465,759))
        sleep(0.5)
    if exists("images/play.png", 20):
        log.info("Character in game already")
    else:
        log.error("ERROR: Cannot find game")
        raise GameError


def create_game(difficulty):
    if exists("images/online.png"):
        log.info("Online found. clicking it.")
        click("images/online.png")
        sleep(20)
    click("images/play.png")
    sleep(0.2)
    click("images/{}.png".format(difficulty))
    create_timeout = 0.5
    while exists("images/ok.png",2):
        log.error("Failed to create a game. Waiting {} minutes to retry.".format(create_timeout))
        click("images/ok.png")
        sleep(60 * create_timeout)
        create_timeout *= 2
        click("images/{}.png".format(difficulty))
    if exists("images/ingame.png", 20):
        log.info("Game creation success.")
    else:
        log.error("Failed to create a game")
        raise GameError


def exit_game():
    log.info("Exiting game.")
    exiting_timeout = 0
    while not exists("images/play.png", 1):
        while not exists("images/save_and_exit.png"):
            if exists("images/tv.png", 1,threshold=0.65,region=TV_REGION):
                log.info("TV exists. Clicking ok.")
                click((1465, 759))
                sleep(0.5)
            exiting_timeout += 1
            if exiting_timeout > 10:
                log.error("Timeout when exiting game")
                raise GameError("Timeout when exiting game")
            pyag.press("esc")
            sleep(0.2)
        click("images/save_and_exit.png")
        sleep(5)


def pre_game_actions():
    log.debug("Pre game actions.")
    # Activate minimap
    sleep(0.2)
    pyag.press('tab')
    sleep(0.2)
    # Activate armor
    pyag.press(ARMOR_KEY)
    sleep(0.2)
    hover(CENTER_LOCATION)
    sleep(0.2)
    pyag.click(button="right")
    sleep(0.2)
    pyag.press(TELEPORT_KEY)
    sleep(0.2)
    # pick up corpse
    pickup_corpse()
    sleep(0.2)
    manage_potions()


def pickup_corpse():
    log.debug("Pickup corpse start.")
    minimap = get_screen(part="minimap")
    corpse_finder = get_object_location_by_color(minimap, [251,0,251], [255,1,255])
    if corpse_finder != (None,None):
        log.info("Corpse found.")
        sleep(1)
        click((1301,659))
        sleep(1)
        global corpses_collected
        corpses_collected += 1
    else:
        log.debug("Corpse not found.")


def manage_potions():
    log.debug("Start manage potions.")
    pyag.press("i")
    manage_potions_timeout = 0
    while True:
        manage_potions_timeout += 1
        log.debug("Manage potions nr" + str(manage_potions_timeout))
        if manage_potions_timeout > 15:
            log.debug("Timeout when clearing eq from potions.")
            break
        if exists("images/healing_potion.png",0.3,region=EQUPMENT_REGION):
            log.debug("Moving health potion")
            hover("images/healing_potion.png",region=EQUPMENT_REGION)
            with pyag.hold('shift'):
                pyag.click()
                sleep(0.1)
        elif exists("images/mana_potion.png",0.3,region=EQUPMENT_REGION):
            log.debug("Moving mana potion")
            hover("images/mana_potion.png",region=EQUPMENT_REGION)
            with pyag.hold('shift'):
                pyag.click()
                sleep(0.1)
        else:
            log.debug("No more potions in equipment.")
            break

    pyag.press("i")


def manage_merc():
    log.debug("Manage merc start.")
    if not exists("images/merc_exists.png",0.2,region=MERC_REGION):
        log.info("Merc do not found. Going to buy one.")
        go_to_destination("images/stash.png", (-80, 35),accepted_distance=15)
        go_to_destination("images/merc_trader.png",(0,40))
        enter_destination("images/merc_trader.png", "images/merc_trader_destination.png","images/resurrect.png",special_shift=(70,200))
        click("images/resurrect.png")
        sleep(0.2)
        pyag.press("esc")
        global merc_resurrected
        merc_resurrected += 1
        go_to_destination("images/merc_trader.png", (50, 50))
        if not exists("images/stash.png",0.3):
            go_to_destination("images/merc_trader.png", (80, 50))
        go_to_destination("images/stash.png", (-80, 35), accepted_distance=15)

def buy_potions():
    log.debug("Buy potions start.")
    pyag.press("~")
    if exists("images/empty_potion.png",0.2,region=POTIONS_BAR_REGION2):
        log.info("Found some empty potion slots, going to Malah")
        pyag.press("~")
        go_to_destination("images/malah.png",(10,30))
        enter_destination("images/malah.png", "images/malah_destination.png","images/trade.png",special_shift=(70,200))

        click("images/trade.png")
        sleep(0.5)
        pyag.press("~")
        while exists("images/empty_potion.png",0.3,region=POTIONS_HEALTH_REGION):
            healing_potion_loc = get_color_location([[19,14,191]],region=TRADER_REGION)
            click(healing_potion_loc,button="right")
            sleep(0.2)
            global life_potions_bought
            life_potions_bought += 1
        while exists("images/empty_potion.png",0.3,region=POTIONS_MANA_REGION):
            mana_potion_loc = get_color_location([[173,25,6]], region=TRADER_REGION)
            click(mana_potion_loc,button="right")
            sleep(0.2)
            global mana_potions_bought
            mana_potions_bought += 1
        pyag.press("esc")
        #go_to_destination("images/malah.png",(20,40),critical=False)
        #go_to_destination("images/malah.png", (70, 20),critical=False)
        sleep(0.1)
        click((1301,1089))
        sleep(1)
        click((1676,657))
        sleep(0.5)
        click((1676, 657))
        sleep(0.5)
        click((1676, 657))
        sleep(0.3)
    else:
        log.info("No empty potion slot find.")
        pyag.press("~")


def get_move_location(diff_location_x,diff_location_y,distance_step):
    distance_min, distance_max = distance_step
    log.debug("Calculating move location from diff_location_x:{},diff_location_y:{},distance_min:{},distance_max:{}".format(diff_location_x,diff_location_y,distance_min,distance_max))
    random_distance = random.randint(distance_min,distance_max)

    # Old calculations
    higher_diff = abs(diff_location_x) if abs(diff_location_x) > abs(diff_location_y) else abs(diff_location_y)
    distance_multiplier = random_distance / higher_diff
    center_x, center_y = CENTER_LOCATION
    old_result_x = int(center_x + (diff_location_x * distance_multiplier))
    old_result_y = int(center_y + (diff_location_y * distance_multiplier))

    # New calculations
    current_lenght = math.sqrt((diff_location_x**2) + (diff_location_y**2))
    distance_factor = random_distance/current_lenght
    result_x = int(center_x + (diff_location_x * distance_factor))
    result_y = int(center_y + (diff_location_y * distance_factor))

    log.info("Move location result: OLD: ({},{}) NEW: ({},{})".format(old_result_x,old_result_y,result_x,result_y))

    return result_x,result_y


# return vector of distance of character from destination point on minimap
# destination can be an image patch or colors range in touple
def get_diff_from_destination(destination, shift=None):
    log.debug("Starting get_diff_from_destination")
    minimap = get_screen(part="minimap")

    char_location = get_object_location_by_color(minimap, [246, 127, 28], [253, 130, 28])
    if char_location == (None,None):
        # If character counter on minimap is under some text then color is different
        char_location = get_object_location_by_color(minimap, [108, 57, 14], [127, 65, 14])
        if char_location == (None, None):
            log.warning("Failed to find character.")
            return None, None

    if type(destination) == str:
        destination_location, *rest = match(destination, own_screenshot=minimap)
    else:
        destination_color1, destination_color2 = destination
        destination_location = get_object_location_by_color(minimap, destination_color1, destination_color2)

    if destination_location == (None,None) or destination_location == None:
        log.warning("Failed to find destination.")
        return None, None

    char_location_x, char_location_y = char_location
    destination_location_x, destination_location_y = destination_location
    if shift is not None:
        shift_x, shift_y = shift
        destination_location_x = destination_location_x + shift_x
        destination_location_y = destination_location_y + shift_y

    diff_location_x = destination_location_x - char_location_x
    diff_location_y = destination_location_y - char_location_y

    log.debug("Char location: {} Destination location: {} Diff location: {},{}".format(char_location, destination_location, diff_location_x, diff_location_y))

    return diff_location_x, diff_location_y


def go_to_destination(destination,shift=None,move_step=(250,350),accepted_distance=20,steps_timeout=30,critical=True):
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
        if exists("images/waypoint.png", 0.01, region=MINIMAP_REGION):
            log.warning("Waypoint image found. Closing it.")
            pyag.press("esc")
        log.debug("waypoint checked.")

        diff_location_x, diff_location_y = get_diff_from_destination(destination, shift=shift)

        # Error counter is used to do not fail function if we do not detect image in single iteration.
        if diff_location_x == None:
            log.warning("Cannot find destination.")
            sleep(0.2)
            if error_counter == 30:
                return False
            else:
                error_counter += 1
                continue
        error_counter = 0

        if abs(diff_location_x) > accepted_distance or abs(diff_location_y) > accepted_distance:
            move_location = get_move_location(diff_location_x,diff_location_y,move_step)
            click(move_location)
        else:
            log.info("Destination reached.")
            return True


def enter_destination(destination,hover_image,final_image,dest_shift=None,special_shift=None):
    enter_max_attempts = 5
    enter_timeout = 0
    while True:
        enter_timeout += 1
        # Check if no other npc was clicked not intentionally
        if exists("images/cancel.png",0.1,region=(856,219,1268,673)):
            pyag.press("esc")
        if enter_timeout > enter_max_attempts:
            log.error("Timeout when entering " + str(destination))
            raise GameError("Timeout when entering " + str(destination))
        if hover_destination(destination,hover_image,dest_shift, special_shift):
            pyag.click()
            sleep(1)
            if exists(final_image,5):
                log.debug("Destination entered correctly.")
                return True


def hover_destination(destination,hover_image,dest_shift=None,special_shift=None):
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
            diff_location_x, diff_location_y = get_diff_from_destination(destination,shift=dest_shift)
            if diff_location_x is not None and diff_location_y is not None:
                break

        center_x, center_y = CENTER_LOCATION

        finding_shifts = [(0,0),(100,0),(-100,0),(0,100),(0,-100),(100,100),(100,-100),(-100,100),(-100,-100),
                          (200,0),(-200,0),(0,200),(0,-200),(200,200),(200,-200),(-200,200),(-200,-200),
                          (200,100),(-200,100),(100,200),(100,-200),(200,-100),(-200,-100),(-100,200),(-100,-200),
                          (0,250),(250,0),(-250,0),(0,-250),(250,250),(250,-250),(-250,250),(-250,-250)]

        if special_shift != None:
            special_shift_x, special_shift_y = special_shift
        else:
            special_shift_x, special_shift_y = (0,0)

        for shift in finding_shifts:
            shift_x, shift_y = shift
            checking_location = (center_x + (diff_location_x * 15) + shift_x + special_shift_x, center_y + (diff_location_y * 15) + shift_y + special_shift_y)
            hover(checking_location)
            if exists(hover_image,0.1):
                log.info("Found {} on location {}".format(hover_image,checking_location))
                return True


def go_to_anya():
    log.info("Going to anya start")
    go_to_destination("images/anya.png", (100, 40))
    go_to_destination("images/anya.png", (20, 45),move_step=(400,450))
    sleep(0.3)
    enter_destination(([0, 239, 239],[0, 243, 243]), "images/nihlak_portal.png","images/ingame.png",special_shift=(-60,0))


def tele_to_pindle():
    log.info("Teleporting to pindle start.")
    tele_timeout = 0
    pyag.press(TELEPORT_KEY)
    sleep(0.1)
    #TELE_CLICK_LOCATION = (1724,367)
    TELE_CLICK_LOCATION = (2080,95)

    while True:
        tele_timeout += 1

        # Workaround - 3 teleportations are enough and changing entrance location sometimes doesnt works
        if tele_timeout >= 4:
            log.info("Teleporting to pindle completed.")
            return True

        if tele_timeout >= 10:
            log.error("Timeout when teleporting to pindle.")
            raise GameError("Timeout when teleporting to pindle.")

        diff_location_x, diff_location_y = get_diff_from_destination(([18, 160, 184], [45, 184, 185]))
        if diff_location_x == None or diff_location_x > 3 or diff_location_y < -3:
            log.debug("Teleporting to pindle number " + str(tele_timeout))
            click(TELE_CLICK_LOCATION, button="right")
            sleep(0.1)
        else:
            log.debug("Teleporting to pindle completed.")
            return True


def kill_pindle():
    log.info("Killing pindle start.")
    pyag.press(ATTACK_KEY)
    sleep(0.1)
    click((1543, 575), button="right")
    sleep(0.2)
    pyag.press(ATTACK_KEY2)
    for i in range(1, 6):
        click((1480, 543), button="right")
    pyag.press(ATTACK_KEY)
    sleep(0.3)
    click((1788, 438), button="right")
    pyag.press(ATTACK_KEY2)
    for i in range(1,12):
        log.info("Attack nr " + str(i))
        if i % 6 == 0:
            pyag.press(ATTACK_KEY)
        if i%2 == 0:
            click((1480, 543), button="right")
        elif i%2 == 1:
            click((1550,613), button="right")
        if i % 6 == 0:
            pyag.press(ATTACK_KEY2)


def collect_loot():
    log.debug("Collect loot start")
    rune_color = (0, 163, 255)
    set_color = (0, 252, 0)
    unique_color = (113, 175, 196)

    collect_timeout = 0
    pyag.press("alt")
    sleep(0.2)
    while True:
        collect_timeout += 1
        if collect_timeout >= 10:
            log.error("Timeout when collecting loot.")
            raise GameError("Timeout when collecting loot.")

        screen = get_screen(part=(600,150,1700,850))
        mask1 = cv.inRange(screen, rune_color, rune_color)
        mask2 = cv.inRange(screen, set_color, set_color)
        mask3 = cv.inRange(screen, unique_color, unique_color)

        ## Merge the mask and crop the red regions
        mask = cv.bitwise_or(mask1, mask2)
        mask = cv.bitwise_or(mask, mask3)
        filtered_bar = cv.bitwise_and(screen, screen, mask=mask)

        # convert the image to grayscale
        gray_image = cv.cvtColor(filtered_bar, cv.COLOR_BGR2GRAY)

        # threshold the image, then perform a series of erosions + dilations to remove any small regions of noise
        thresh = cv.threshold(gray_image, 5, 255, cv.THRESH_BINARY)[1]

        # find contours in thresholded image, then grab the largest one
        cnts = cv.findContours(thresh.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        if not cnts:
            #Checking charms
            charm, *rest = match("images/charm.png",threshold=0.6, own_screenshot=screen)
            if charm == (None, None) or charm == None:
                log.info("No more items found.")
                break
            else:
                item_x, item_y = charm
        else:
            c = max(cnts, key=cv.contourArea)

            item_x, item_y = tuple(c[c[:, :, 1].argmax()][0])

        item = item_x + 600, item_y + 150

        log.info("Collecting item on location: " + str(item))
        click(item)
        sleep(1)


def get_equipment_item():
    log.debug("get_equipment_item start")
    occupied_equipment = image_mask("images/empty_equipment.png",region=EQUPMENT_REGION,inverted=True)
    cnts = cv.findContours(occupied_equipment.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    if not cnts:
        log.info("No equipment found.")
        return None,None

    c = max(cnts, key=cv.contourArea)

    item_x, item_y = tuple(c[c[:, :, 1].argmax()][0])
    item = item_x + 1696, item_y + 731
    log.info("Found item on location: " + str(item))
    return item


def store_items():
    log.debug("Store items start")
    check_equipment = False
    if USE_MERC:
        if not exists("images/merc_exists.png", 0.2, region=MERC_REGION):
            check_equipment = True
    pyag.press("i")
    sleep(0.1)
    if get_equipment_item() != (None,None) or check_equipment:
        pyag.press("i")
        log.info("Some items to stash found.")

        enter_destination("images/stash.png", "images/stash_destination.png","images/stash_inside.png",special_shift=(70, 200))

        # Switch to personal tab
        click(STASH_LOCATIONS[0])
        sleep(0.1)

        # Get gold from other stash bars if there are less than 100k in personal
        if exists("images/emptygold.png",0.1,region=EMPTY_GOLD_REGION):
            log.info("Not enough gold. Gathering from other stash bars.")
            for bar_number in range(1,3):
                log.info("Switching stash bar to " + str(bar_number))
                click(STASH_LOCATIONS[bar_number])
                sleep(0.1)
                if not exists("images/emptygold.png", 0.1, region=EMPTY_GOLD_REGION):
                    log.info("Collecting gold from stash bar " + str(bar_number))
                    click("images/windraw.png",region=GOLD_REGION)
                    sleep(0.1)
                    for i in range(1,8):
                        pyag.press("backspace")
                        sleep(0.02)
                    pyag.typewrite("400000")
                    pyag.press("enter")
                    log.info("Gold collected.")
                    break
            else:
                log.error("Lack of gold. Exiting.")
                exit(0)
            log.info("Sending gold to personal bar.")
            sleep(0.1)
            click(STASH_LOCATIONS[0])
            sleep(0.1)
            click("images/windraw.png", region=CHAR_GOLD_REGION)
            sleep(0.1)
            pyag.press("enter")
            sleep(0.1)


        items_storing_timeout = 0
        current_stash = 0
        previous_item_to_store = (None,None)
        while True:
            items_storing_timeout += 1
            if items_storing_timeout >= 16:
                log.error("Timeout when storing items.")
                raise GameError("Timeout when storing items.")

            item_to_store = get_equipment_item()
            if item_to_store == (None,None):
                log.info("All items stored.")
                pyag.press("esc")
                break
            elif item_to_store == previous_item_to_store:
                log.info("Stash bar is full, switching to next bar.")
                previous_item_to_store = (None, None)
                current_stash += 1
                if current_stash > 3:
                    log.error("Whole stash is full. Exiting")
                    sleep(6000)
                    exit(0)
                click(STASH_LOCATIONS[current_stash])
            else:
                hover(item_to_store)
                sleep(0.1)
                found_item_description,rarity = get_item_description()
                log.info("Item description: " + str(found_item_description))
                item_name = found_item_description.partition('\n')[0]
                if rarity != "unknown" and item_classification(item_name,rarity):
                    global found_items_list
                    found_items_list.append(item_name)
                    log.info("Store item: " + str(item_name))
                    sleep(0.1)
                    with pyag.hold('ctrl'):
                        pyag.click()
                        sleep(0.1)
                else:
                    global ignored_items_list
                    ignored_items_list.append(item_name)
                    log.info("Ignored item: " + str(item_name))
                    sleep(0.1)
                    pyag.click()
                    sleep(0.1)
                    hover(CENTER_LOCATION)
                    pyag.click()
                    sleep(0.1)
                previous_item_to_store = item_to_store
    else:
        pyag.press("i")


def item_classification(item_name,rarity):
    global good_items
    for good_item in good_items[rarity]:
        log.info("Classification of {} compared to found item {}".format(good_item,item_name))
        similarity_ratio = SequenceMatcher(None, good_item.lower(), item_name.lower()).ratio()
        log.info("Classification ratio: " + str(similarity_ratio))
        if similarity_ratio > 0.8:
            return True
    else:
        return False

def get_item_region():
    screen = get_screen(part=(1380,0,1142,1440))
    masked_screen = multimask(screen, [62,62,62])

    img_gray = cv.cvtColor(masked_screen, cv.COLOR_BGR2GRAY)

    thresh = cv.threshold(img_gray, 45, 255, cv.THRESH_BINARY)[1]

    # find contours in thresholded image, then grab the largest one
    cnts = cv.findContours(thresh.copy(), cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    c = max(cnts, key=cv.contourArea)
    x, y, w, h = cv.boundingRect(c)
    x = x + 1380

    log.debug("Found item contour: {},{},{},{}".format(x, y, w, h))

    #screen_copy = screen.copy()
    #cv.drawContours(image=screen_copy, contours=cnts, contourIdx=-1, color=(0, 255, 0), thickness=2,lineType=cv.LINE_AA)
    #cv.rectangle(screen_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
    #cv.rectangle(screen_copy, (x, y), (x + w, y + 50), (255, 0, 0), 2)

    #cv.imshow("screen_copy",  screen_copy)
    #cv.waitKey(0)

    return x, y, w, h


def get_item_rarity(item_region):
    x,y,w,h = item_region
    item_name_region = x,y,w,50

    if get_color_location([GOLD_TEXT],region=item_name_region) != (None,None):
        rarity = "unique"
    elif get_color_location([GREEN_TEXT],region=item_name_region) != (None,None):
        rarity = "set"
    elif get_color_location([ORANGE_TEXT], region=item_name_region) != (None,None):
        rarity = "rune"
    elif get_color_location([BLUE_TEXT], region=item_name_region) != (None,None):
        rarity = "magic"
    else:
        rarity = "unknown"
    return rarity


def get_item_description():
    item_region = get_item_region()
    screen = get_screen(part=(item_region))
    masked_screen = multimask(screen, [GREEN_TEXT,WHITE_TEXT,BLUE_TEXT,GOLD_TEXT,RED_TEXT,ORANGE_TEXT])

    #cv.imshow("masked_screen",  masked_screen)
    #cv.waitKey(0)

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
    contours, hierarchy = cv.findContours(dilation, cv.RETR_EXTERNAL,cv.CHAIN_APPROX_NONE)

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
            text = text.replace(c,"O")
    #cv.imshow("screen_copy",  rect)
    #cv.waitKey(0)

    # Get item rarity
    rarity = get_item_rarity(item_region)
    log.info("Item rarity: " + str(rarity))

    log.debug("Full item description: " + str(text))
    return text,rarity


####### TESTS

def hover_test(image,special_shift):
    diff_location_x, diff_location_y = get_diff_from_destination(image)
    center_x, center_y = CENTER_LOCATION
    log.info("diff_location_x: {} diff_location_y: {}".format(diff_location_x,diff_location_y))
    special_shift_x, special_shift_y = special_shift
    checking_location = (center_x + (diff_location_x * 15) + special_shift_x, center_y + (diff_location_y * 16)+ special_shift_y)
    hover(checking_location)

# Login
# Select character
# Create game
# Pre-run actions:
# - Find char body - loot body
# - not empty equipment - stash items
# - not full potions belt - buy potions
# - Items requires repair - repair items
# - go to wp
# Run actions
# - find next location / care for resources
# - find goal monsters / care for resources
# - clear additional mobs / care for resources
# - kill mobs / care for resources
# - loot items
# - back to town
# next run or next game

# Rewards:
# Find entrance on minimap +5
# Locate entrance by cursor +5
# enter correct entrance +20
# bonus: 100 - time required
#
# penalty:
# Do not find in correct time (100 seconds timeout) -20
# Die -30

sleep(2)

# Vars initialization
game_number = 0
issues_counter = 0
merc_resurrected = 0
corpses_collected = 0
life_potions_bought = 0
mana_potions_bought = 0
correct_finish = 0
issues_list = []
times_list = []
stop_potioner = False
found_items_list = []
ignored_items_list = []

#just potioner
#potioner_thread = threading.Thread(target=potioner)
#potioner_thread.start()
#sleep(1200)
#stop_potioner = True
#potioner_thread.join()
#hover_test("images/merc_trader.png",special_shift=(70,200))0

#game_restore()
# exit(0)

good_items = {}
# Load items lists
for item_rarity in ["unique","set","rune","magic"]:
    with open("items/" + item_rarity + ".txt") as file:
        file_lines = [line.rstrip() for line in file]
        good_items[item_rarity] = [re.sub(r"(\w)([A-Z])", r"\1 \2", line.split(" ")[2]) for line in file_lines if line.startswith("[Name]")]
        log.info("Item rarity {}:".format(item_rarity))
        log.info(good_items[item_rarity])

# Main loop
while game_number < games_max:
    try:
        game_number += 1
        potioner_thread = None
        log.info("")
        log.info("---------------------------------------------------------------------")
        log.info("Starting game number " + str(game_number) + ". Current number of issues: " + str(issues_counter))
        log.info("---------------------------------------------------------------------")
        log.info("Issues list: " + str(issues_list))
        log.info("Corpses collected: " + str(corpses_collected))
        log.info("Merc resurrections: " + str(merc_resurrected))
        log.info("Life/mana potions used: {}/{}".format(life_potions_bought,mana_potions_bought))
        log.info("Correct finish: " + str(correct_finish))
        log.info("Found items list: " + str(found_items_list))
        log.info("Ignored items list: " + str(ignored_items_list))
        log.info("---------------------------------------------------------------------")
        game_time_start = datetime.datetime.now()
        start_game()
        create_game(difficulty)
        try:
            pre_game_actions()
            buy_potions()
            go_to_destination("images/stash.png", (-45, 5))
            store_items()
            if USE_MERC:
                manage_merc()
                pass
            go_to_anya()
            stop_potioner = False
            potioner_thread = threading.Thread(target=potioner, args=(lambda: stop_potioner,))
            potioner_thread.start()
            tele_to_pindle()
            kill_pindle()
            collect_loot()
            log.info("Game finished correctly.")
            correct_finish += 1
        except GameError as e:
            if exists("images/tv.png",1,threshold=0.65, region=TV_REGION):
                log.info("TV exists. Clicking ok.")
                click((1465, 759))
                sleep(0.5)
            log.error(e, exc_info=True)
            log.exception('Exception found.')
            issues_counter += 1
            issues_list.append(e)
        finally:
            if potioner_thread is not None:
                log.info("Disabling potioner thread.")
                stop_potioner = True
                potioner_thread.join()
                log.info("Potioner finished.")
            exit_game()
            game_time_stop = datetime.datetime.now()
            game_time = game_time_stop - game_time_start
            log.info("Game took: " + str(game_time.seconds))
            continue
    except Exception as e:
        log.error(e, exc_info=True)
        log.exception('Game crashed. Restoring it')
        issues_counter += 1
        issues_list.append(e)
        game_restore()