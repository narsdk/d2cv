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

#pyag.FAILSAFE = False

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
MINIMAP_REGION = (0,50,860,485)
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

# POTIONER
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

# POTIONER
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

# POTIONER
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

# POTIONER
# Dring mana or health potion
def drink_potion(type):
    if type == "health":
        pyag.press(str(random.randint(1,2)))
    elif type == "reju":
        pyag.press("2")
    elif type == "mana":
        pyag.press(str(random.randint(3,4)))

# ABADONED AND REPLACED - DONE
# Random tele or move on lock
def random_on_lock(old_map, new_map, button = "right"):
    map_diff = get_map_difference(old_map, new_map)

    if map_diff < 2500:
        click(random.choice(list(move_directions.values())), button)
        sleep(1)


# ABADONED
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


# RESTORER
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


# GAME CREATOR - DONE
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

# GAME CREATOR - DONE
def create_game(difficulty):
    if exists("images/online.png"):
        log.info("Online found. clicking it.")
        click("images/online.png")
        sleep(20)
    click("images/play.png")
    sleep(0.2)
    click("images/{}.png".format(difficulty))
    create_timeout = 0.25
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

# GAME CREATOR - DONE
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

# TOWN MANAGEMENT
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

# TOWN MANAGEMENT
def pickup_corpse():
    log.debug("Pickup corpse start.")
    minimap = get_screen(part=MINIMAP_REGION)
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

# TOWN MANAGEMENT
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

# TOWN MANAGEMENT
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

# TOWN MANAGEMENT
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

# MAP TRAVELER - DONE
def get_move_location(diff_location_x,diff_location_y,distance_step):
    distance_min, distance_max = distance_step
    log.debug("Calculating move location from diff_location_x:{},diff_location_y:{},distance_min:{},distance_max:{}".format(diff_location_x,diff_location_y,distance_min,distance_max))
    random_distance = random.randint(distance_min,distance_max)
    center_x, center_y = CENTER_LOCATION

    # New calculations
    current_lenght = math.sqrt((diff_location_x**2) + (diff_location_y**2))
    distance_factor = random_distance/current_lenght
    result_x = int(center_x + (diff_location_x * distance_factor))
    result_y = int(center_y + (diff_location_y * distance_factor))

    log.debug("Move location result: ({},{})".format(result_x,result_y))

    return result_x,result_y

# MAP TRAVELER - DONE
def get_char_location(minimap):
    char_location = (None,None)
    fail_counter = 0
    while char_location == (None,None):
        char_location = get_object_location_by_color(minimap, [159, 85, 21],[253, 136, 43])
        if char_location == (None, None):
            # If character counter on minimap is under some text then color is different
            char_location = get_object_location_by_color(minimap, [193, 104, 25],[253, 136, 33])
            if char_location == (None, None):
                log.warning("Failed to find character.")
                fail_counter += 1
                sleep(0.1)
                if fail_counter > 5:
                    return (433, 248)
    return char_location


# MAP TRAVELER - DONE
# return vector of distance of character from destination point on minimap
# destination can be an image patch or colors range in touple
def get_diff_from_destination(destination, shift=None,filter=False):
    log.debug("Starting get_diff_from_destination")
    minimap = get_screen(part=MINIMAP_REGION)

    char_location = get_char_location(minimap)

    if type(destination) == str:
        destination_location, *rest = match(destination, own_screenshot=minimap)
    else:
        destination_color1, destination_color2 = destination
        destination_location = get_object_location_by_color(minimap, destination_color1, destination_color2, filter)

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

# CHARACTER - DONE
def go_to_destination(destination,shift=None,move_step=(250,350),accepted_distance=20,steps_timeout=30,critical=True, filter=False, button="left",move_sleep=0):
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

        diff_location_x, diff_location_y = get_diff_from_destination(destination, shift=shift, filter=filter)

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
            click(move_location,button=button)
            sleep(move_sleep)
        else:
            log.info("Destination reached.")
            return True

# CHARACTER - DONE
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

# CHARACTER - DONE
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
            if exists(hover_image,0.05):
                log.info("Found {} on location {}".format(hover_image,checking_location))
                return True

# TASKS - DONE
def go_to_anya():
    log.info("Going to anya start")
    go_to_destination("images/anya.png", (100, 40))
    go_to_destination("images/anya.png", (20, 45),move_step=(400,450))
    sleep(0.3)
    enter_destination(([0, 239, 239],[0, 243, 243]), "images/nihlak_portal.png","images/ingame.png",special_shift=(-60,0))

# TASKS - DONE
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
        if diff_location_x is None or diff_location_x > 3 or diff_location_y < -3:
            log.debug("Teleporting to pindle number " + str(tele_timeout))
            click(TELE_CLICK_LOCATION, button="right")
            sleep(0.1)
        else:
            log.debug("Teleporting to pindle completed.")
            return True

# TASKS - DONE
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

# LOOT_COLLECTOR
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

# LOOT_COLLECTOR
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

# LOOT_COLLECTOR
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

# LOOT_COLLECTOR
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

# LOOT_COLLECTOR
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

# LOOT_COLLECTOR
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

# LOOT_COLLECTOR
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

# Development Util
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

# MAPPER - DONE
def get_meph_map(minimap,mode="full"):
    minimap_hsv = cv.cvtColor(minimap, cv.COLOR_BGR2HSV)
    # walls colors
    lower_map = np.array([0, 16, 27])
    upper_map = np.array([32, 133, 106])
    # other borders colors
    # original
    # lower_map2 = np.array([14, 6, 44])
    # upper_map2 = np.array([45, 87, 141])

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


    # Hide merc
    merc_rectangle = np.array([[[30,0],[111,0],[111,92],[30,92]]],dtype=np.int32)
    cv.fillPoly(full_mask, merc_rectangle, (0, 0, 0))

    #full_mask = clear_map(full_mask, 30)

    target = cv.bitwise_and(minimap, minimap, mask=full_mask)

    return full_mask,target

# MAP TRAVELER - DONE
def get_meph_start_direction(map, minimap):
    map_canny = cv.Canny(map, 50, 200, None, 3)

    # cv.imshow("map", map)
    # cv.waitKey()
    #cv.imshow("minimap_mask2", minimap_mask2)

    def change_canny_min(val):
        mask_canny = cv.Canny(map, 50, val)
        cv.imshow(window_name, mask_canny)


    # window_name = "map"
    # cv.imshow(window_name, mask_canny)
    # cv.createTrackbar('min', window_name, 0, 500, change_canny_min)
    # cv.waitKey(0)

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

# CHARACTER - done
def teleport_to(direction,distance,sleep_time=0.25, offset=None, mode="normal"):
    log.info("Teleport start")
    direction_location_x, direction_location_y = move_directions[direction]
    center_x, center_y = CENTER_LOCATION

    if offset is not None:
        direction_location_x, direction_location_y = direction_location_x + offset[0], direction_location_y + offset[1]
    teleport_location = get_move_location(direction_location_x - center_x, direction_location_y - center_y, (distance,distance))

    if mode == "normal":
        click(teleport_location,button="right")
    elif mode == "continous":
        pyag.moveTo(teleport_location)
        pyag.mouseDown(button='right')
    sleep(sleep_time)
    if mode == "continous":
        pyag.mouseUp(button='right')
    log.info("Teleport end")

# ABADONED
def get_out_direction(meph_map,meph_mask,char_possition):
    _,_,minimap_res_x,minimap_res_y = MINIMAP_REGION
    for direction in move_directions:
        dir_location = direction_resolver(direction,(minimap_res_x,minimap_res_y))
        log.info("Minimap direction {} location {}".format(direction,dir_location))
    output = meph_map.copy()
    contours, hierarchy = cv.findContours(meph_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    if len(contours) != 0:
        # draw in blue the contours that were founded
        #cv.drawContours(output, contours, -1, 255, 3)

        # find the biggest countour (c) by the area
        c = max(contours, key=cv.contourArea)
        cv.drawContours(output, c, -1, 255, 3)
        (x,y),(MA,ma),angle = cv.fitEllipse(c)
        log.info("(x:{},y:{}),(MA:{},ma:{}),angle:{}".format(x,y,MA,ma,angle))
        cv.circle(output,(int(x),int(y)),5,[255,0,0],-1)
        cv.circle(output, (int(MA), int(ma)), 5, [0, 255, 0], -1)
        log.info("Angle: " + str(angle))
        #x, y, w, h = cv.boundingRect(c)

        # draw the biggest contour (c) in green
        #cv.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)

    #cv.imshow("Result", np.hstack([meph_map, output]))
    #cv.waitKey(0)

# MAPPER - ABADONED
def clear_map(map,min_size):
    # find all your connected components (white blobs in your image)
    nb_components, output, stats, centroids = cv.connectedComponentsWithStats(map, connectivity=8)
    # connectedComponentswithStats yields every seperated component with information on each of them, such as size
    # the following part is just taking out the background which is also considered a component, but most of the time we don't want that.
    sizes = stats[1:, -1];
    nb_components = nb_components - 1

    # your answer image
    map2 = np.zeros((output.shape))
    # for every component in the image, you keep it only if it's above min_size
    for i in range(0, nb_components):
        if sizes[i] >= min_size:
            map2[output == i + 1] = 255

    ret, map3 = cv.threshold(map2, 128, 255, cv.THRESH_BINARY)

    #cv.imshow("Cleared Map", np.hstack([map, map2, map3]))
    #cv.waitKey(0)

    return map3


### ABADONED
def teleporter():
    time.sleep(5)
    tele_locations = [(10,10),(2550,10),(2550,1100),(10,1100)]
    tele_nr = 1

    minimap = get_screen(part=MINIMAP_REGION)
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

        minimap = get_screen(part=MINIMAP_REGION)

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


# MAP TRAVELER - DONE
def find_line(meph_map, direction="tl", type="terain"):
    meph_map = cv.cvtColor(meph_map, cv.COLOR_GRAY2BGR)
    map_lined_normal = meph_map.copy()

    map_blured = cv.GaussianBlur(map_lined_normal, (9, 9), 0)

    thresh, map_blured = cv.threshold(map_blured, 50, 255, cv.THRESH_BINARY)
    map_blured_gray = cv.cvtColor(map_blured, cv.COLOR_BGR2GRAY)

    cnts,hierarchy = cv.findContours(map_blured_gray.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    #cnts = imutils.grab_contours(cnts)
    #contoured_image = cv.drawContours(map_blured,cnts,-1, (0,255,0), 3)

    list_of_pts = []
    for ctr in cnts:
        list_of_pts += [pt[0] for pt in ctr]

    ctr = np.array(list_of_pts).reshape((-1, 1, 2)).astype(np.int32)
    hull = cv.convexHull(ctr)

    #log.info("cnts: " + str(cnts))
    #log.info("ctr: " + str(cnts))
    #log.info("hull: " + str(cnts))

    # create hull array for convex hull points
    #hull = []

    # calculate points for each contour
    #for i in range(len(cnts)):
        # creating convex hull object for each contour
    #    hull.append(cv.convexHull(cnts[i], False))

    # create an empty black image
    #drawing = np.zeros((map_blured.shape[0], map_blured.shape[1], 3), np.uint8)
    #cv.drawContours(map_blured, hull, -1, (255, 0, 0) , 4, cv.FILLED)
    # draw contours and hull points
    # for i in range(len(cnts)):
    #     color_contours = (0, 255, 0)  # green - color for contours
    #     #color = (255, 0, 0)  # blue - color for convex hull
    #
    #     # draw ith contour
    #     cv.drawContours(map_blured, cnts, i, color_contours, 1, 8, hierarchy)
    #     # draw ith convex hull object
    #     #cv.drawContours(drawing, hull, i, color, 1, 8)

    ########################## FEATURES

    map_mask = np.zeros((map_blured_gray.shape[0],map_blured_gray.shape[1]), np.uint8)
    #map_mask = cv.cvtColor(map_mask,cv.COLOR_GRAY2BGR)
    #map_mask = cv.rectangle(map_mask,(30,30),(55,70),255,-1)
    # map_slicer = {
    #     "tl": minimap[148:248, 336:436],
    #     "tr": minimap[148:248, 436:536],
    #     "dr": minimap[248:348, 436:536],
    #     "dl": minimap[248:348, 336:436]
    # }
    if type == "terain":
        mask_direction_poly = {
            "tl": np.array([[(15, 65), (40, 45), (80, 65), (55, 85)]]), # done
            "tr": np.array([[(15, 70), (40, 90), (80, 60), (55, 40)]]), # done
            "dl": np.array([[(50, 00), (80, 30), (40, 50), (10, 20)]]), # done
            "dr": np.array([[(40, 10), (15, 30), (55, 60), (80, 40)]]) # done
        }
    elif type == "wall":
        mask_direction_poly = {
            "tl": np.array([[(100, 80), (70, 100), (100, 100)]]),  # done
            "tr": np.array([[(0, 80), (30, 100), (0, 100)]]),  # done
            "dl": np.array([[(70, 0), (100, 20), (100, 0)]]),  # done
            "dr": np.array([[(0, 0), (0, 20), (30, 0)]])  # done
        }
    map_mask = cv.fillPoly(map_mask, pts=[mask_direction_poly[direction]], color=(255,255,255))

    masked_mask = cv.bitwise_and(map_blured_gray,map_mask)

    # Copy edges to the images that will display the results in BGR
    # map_lined = cv.cvtColor(map_canny, cv.COLOR_GRAY2BGR)

    #map_canny = cv.Canny(map_part, 50, 200, None, 3)

    linesP = cv.HoughLinesP(masked_mask, 1, np.pi / 180, 10, None, 10, 10)

    longest_line_size = 0
    if linesP is not None:
        for i in range(0, len(linesP)):
           l = linesP[i][0]
           #cv.line(map_lined_normal, (l[0], l[1]), (l[2], l[3]), (0, 0, 255), 3, cv.LINE_AA)
           line_size = math.sqrt((((l[0] - l[2]) ** 2) + ((l[1] - l[3]) ** 2)))
           if line_size > longest_line_size:
               longest_line_size = line_size
               longest_line = l
        cv.line(map_lined_normal, (longest_line[0], longest_line[1]), (longest_line[2], longest_line[3]), (0, 0, 255), 3, cv.LINE_AA)


    log.debug("Longest line size on map is " + str(longest_line_size))


    # cv.imshow("mask",np.hstack([map_lined_normal,masked_mask]))
    # cv.waitKey()
    #mask = cv.cvtColor(mask,cv.COLOR_GRAY2BGR)

    # feature_params = dict(maxCorners=500,
    #                       qualityLevel=0.2,
    #                       minDistance=10,
    #                       blockSize=15,
    #                       mask=map_mask,
    #                       useHarrisDetector=True
    #                       )
    #
    # corners = cv.goodFeaturesToTrack(map_blured_gray, **feature_params)
    # if corners is not None:
    #     for x, y in np.float32(corners).reshape(-1, 2):
    #         cv.circle(map_lined_normal, (int(x), int(y)), 10, (0, 255, 0), 1)
    #     corners_number = len(corners)
    # else:
    #     corners_number = 0

    border = np.full((meph_map.shape[0],1,3),(0,0,255),np.float32)
    map_mask = cv.cvtColor(map_mask,cv.COLOR_GRAY2BGR)
    masked_mask = cv.cvtColor(masked_mask,cv.COLOR_GRAY2BGR)

    # cv.imshow("test", np.hstack([meph_map,border,map_mask,border,masked_mask,border,map_lined_normal]))
    # cv.waitKey(0)

    ############################# FEATURES KEYPOINTS

    # orb = cv.ORB_create(500)
    # keypoints1, descriptors1 = orb.detectAndCompute(map_blured_gray, None)
    # map_lined_normal = cv.drawKeypoints(map_lined_normal, keypoints1, outImage=np.array([]), color=(255, 0, 0), flags=cv.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    # c = max(cnts, key=cv.contourArea)
    # extLeft = tuple(c[c[:, :, 0].argmin()][0])
    # extRight = tuple(c[c[:, :, 0].argmax()][0])
    # extTop = tuple(c[c[:, :, 1].argmin()][0])
    # extBot = tuple(c[c[:, :, 1].argmax()][0])
    # cv.drawContours(map_blured, [c], -1, (0, 255, 255), 1)
    # cv.circle(map_blured, extLeft, 8, (0, 0, 255), -1)
    # cv.circle(map_blured, extRight, 8, (0, 255, 0), -1)
    # cv.circle(map_blured, extTop, 8, (255, 0, 0), -1)
    # cv.circle(map_blured, extBot, 8, (255, 255, 0), -1)

    return map_lined_normal, longest_line_size

# MAPPER - DONE
def check_direction(minimap, current_direction,turn=None, type="terain"):
    #character location (434, 248)

    # Old possitions:
    # map_slicer = {
    #     "tl": minimap[148:248, 336:436],
    #     "tr": minimap[148:248, 436:536],
    #     "dr": minimap[248:348, 436:536],
    #     "dl": minimap[248:348, 336:436]
    # }

    map_slicer = {
        "tl": minimap[148:248, 336:436],
        "tr": minimap[152:252, 430:530],
        "dr": minimap[240:340, 430:530],
        "dl": minimap[242:342, 338:438]
    }

    # for mode in [cv.RETR_EXTERNAL,cv.RETR_LIST,cv.RETR_CCOMP,cv.RETR_TREE,cv.RETR_FLOODFILL]:
    #     for method in [cv.CHAIN_APPROX_NONE, cv.CHAIN_APPROX_SIMPLE, cv.CHAIN_APPROX_TC89_L1, cv.CHAIN_APPROX_TC89_KCOS]:
    #find_external_points(minimap)
    # ext_tl, corners_tl = find_external_points(map_slicer["tl"])
    # ext_tr, corners_tr = find_external_points(map_slicer["tr"])
    # ext_dl, corners_dl = find_external_points(map_slicer["dl"])
    # ext_dr, corners_dr = find_external_points(map_slicer["dr"])
    # empty = np.ones((ext_dr.shape[0], ext_dr.shape[1], 3), np.uint8)

    #cv.imshow("minimap", np.hstack([map_slicer["tl"],map_slicer["tr"],map_slicer["dl"],map_slicer["dr"]]))
    # cv.imshow("test", np.hstack([ext_tl, empty, ext_tr, empty, ext_dl, empty, ext_dr]))
    # cv.waitKey(0)

    if turn == "left":
        screen_direction = direction_numbers[(direction_numbers.index(current_direction) - 1) % 4]
    elif turn == "right":
        screen_direction = direction_numbers[(direction_numbers.index(current_direction) - 1) % 4]
    else:
        screen_direction = current_direction
    log.debug("Checking screen from direction " + str(screen_direction))
    map_part = map_slicer[screen_direction]

    test_scr, line_size = find_line(map_part, screen_direction, type)
    log.visual(VisualRecord(("Checking direction: {} turn: {}".format(current_direction, turn)), [test_scr], fmt="png"))
    # cv.imshow("test", np.hstack([test_scr]))
    # cv.waitKey(0)

    if line_size > 0:
        return True
    else:
        return False


# ABADONED
def find_new_direction(current_direction, minimap, old_minimap, block_counter, changed, last_moves):
    log.info("Finding new direction")

    # Check if character stuck
    if get_map_difference(old_minimap, minimap) < 1000:
        character_blocked = True
    else:
        character_blocked = False
    new_terain = check_direction(minimap, current_direction, turn="left")

    last_changes = sum(map(lambda x: x[2] == 3, last_moves[-15:]))
    new_terain_last5 = sum(map(lambda x: x[3] == True, last_moves[-5:]))

    if new_terain_last5 >= 5:
        log.info("New terain since {} loops, going straight.".format(new_terain_last5))

    if not character_blocked and not new_terain:
        block_counter = 0
        changed = 0
        direction_result = current_direction
        log.info("Continuing with old direction " + str(direction_result))

    elif not character_blocked and new_terain:
        block_counter = 0
        if changed < 1 and last_changes < 2 and new_terain_last5 < 5:
            direction_result = direction_numbers[(direction_numbers.index(current_direction) - 1) % 4]
            changed = 3
            log.info("Found new direction. Next tele direction is " + str(direction_result))
        else:
            direction_result = current_direction
            log.info("Round workaround with old direction " + str(direction_result))
            changed -= 1

    elif character_blocked and not new_terain:
        changed = 0
        if block_counter < 1:
            block_counter += 1
            direction_result = current_direction
            log.info("Character stuck. Trying again " + str(direction_result))
        else:
            direction_result = direction_numbers[(direction_numbers.index(current_direction) + 1) % 4]
            block_counter = 0
            log.info("Character stuck. Next tele direction is " + str(direction_result))

    elif character_blocked and new_terain:
        if changed < 1 and last_changes < 2:
            direction_result = direction_numbers[(direction_numbers.index(current_direction) - 1) % 4]
            changed += 1
            block_counter += 1
            log.info("Found new direction when character is blocked. Next tele direction is " + str(direction_result))
        elif block_counter >= 2:
            block_counter = 0
            direction_result = direction_numbers[(direction_numbers.index(current_direction) + 1) % 4]
            log.info("Found new direction but we do not want to do a round, its blocked also.")
        else:
            block_counter += 1
            direction_result = current_direction
            log.info("Character stuck. Trying again " + str(direction_result))

    last_moves.append((direction_result,block_counter,changed, new_terain))
    #cv.imshow("Cleared Map", np.hstack([minimap, old_minimap]))
    #cv.waitKey(0)

    log.info("Finding new direction end")
    return direction_result, block_counter, changed, last_moves

# MAP_TRAVELER - DONE
def find_new_direction2(current_direction, minimap, old_minimap, last_moves):
    # Define main factors - character blocked comparing to last move, wall on forward and wall on left (no new terain to go)
    character_blocked = get_map_difference(old_minimap, minimap) < 1000
    forward_terain = check_direction(minimap, current_direction)
    forward_wall = check_direction(minimap, current_direction, type="wall")
    left_terain = check_direction(minimap, current_direction, turn="left")
    left_wall = check_direction(minimap, current_direction, turn="left", type="wall")

    turned_right = turned_left = False

    if forward_wall and not forward_terain and left_wall and not left_terain and character_blocked:
        direction_result = direction_numbers[(direction_numbers.index(current_direction) + 1) % 4]
        turned_right = True
    elif character_blocked and len(last_moves) > 0 and last_moves[-1][3] == True and last_moves[-1][1] == False:
        direction_result = direction_numbers[(direction_numbers.index(current_direction) + 1) % 4]
        turned_right = True
    elif left_terain and sum(map(lambda x: x[2] == True, last_moves[-2:])) == 0 and sum(map(lambda x: x[4] == True, last_moves[-5:])) < 5:
        direction_result = direction_numbers[(direction_numbers.index(current_direction) - 1) % 4]
        turned_left = True
    else:
        direction_result = current_direction


    last_moves.append((direction_result, turned_right, turned_left, character_blocked, left_terain))
    return direction_result, last_moves

# MAPPER - done
def get_entrance_location(known_entrance, minimap):
    log.debug("Checking entrance")
    #result = get_object_location_by_color(minimap, [220, 62, 139],[235, 101, 223], filter=True)
    #result = get_object_location_by_color(minimap, [122, 44, 97],[177, 70, 173], filter=False)
    result = get_object_location_by_color(minimap, [149, 41, 98], [235, 101, 223], filter=True)

    if known_entrance is not None and result != (None,None):
        new_entrance = get_meph_entrance_image(minimap)
        if new_entrance.shape != known_entrance.shape:
            return (None ,None)
        entrance_diff_image = cv.bitwise_and(new_entrance, cv.bitwise_not(known_entrance))
        entrance_diff = cv.findNonZero(entrance_diff_image)
        if entrance_diff is None:
            entrance_diff = 0
        else:
            entrance_diff = len(entrance_diff)
        log.visual(VisualRecord(("Entrance difference is: {}".format(entrance_diff)), [result, known_entrance], fmt="png"))
        log.debug("entrance diff: " + str(entrance_diff))
        # cv.imshow("new_entrance", np.hstack([entrance_diff_image]))
        # cv.waitKey()
        if entrance_diff < 800:
            return (None, None)

    return result

# MAPPER - done
def get_meph_entrance_image(minimap):
    meph_map_masked, meph_map_target = get_meph_map(minimap, mode="full")
    entrance_location = get_entrance_location(None,minimap)
    entrance_image = meph_map_masked[entrance_location[1]-80:entrance_location[1]+80,entrance_location[0]-80:entrance_location[0]+80]
    return entrance_image

# MAP_TRAVELER - DONE #TODO: SHOULD BE CHANGED TO GO_TO_DESTINATION
def goto_entrance():
    log.info("Going to located entrance")
    timeout_counter = 0
    while True:
        minimap = get_screen(part=MINIMAP_REGION)
        char_location = get_char_location(minimap)
        old_map = get_easy_map(minimap,char_location) # REPLACE BY SOMETHING NEW

        if timeout_counter > 20:
            log.error("Timeout when going to entrance.")
            return False, None

        # Check entrance possition
        entrance_location = get_entrance_location(None, minimap)
        if entrance_location == (None,None):
            timeout_counter += 1
            sleep(0.3)
            log.warning("Cannot find entrance location nr " + str(timeout_counter))
            continue

        log.info("Character location: {} Entrance location: {}".format(char_location,entrance_location))

        # Go to entrance possition
        entrance_x, entrance_y = entrance_location
        char_x, char_y = char_location
        if abs(entrance_x - char_x) > 40 or abs(entrance_y - char_y) > 40:
            tele_location = get_tele_location(char_location, entrance_location)
            click(tele_location, button='right')
            time.sleep(0.7)
            minimap = get_screen(part=MINIMAP_REGION)
            new_map = get_easy_map(minimap, char_location) # REPLACE BY SOMETHING NEW
            if timeout_counter > 5:
                random_on_lock(old_map, new_map) # REPLACE BY SOMETHING NEW

        # if its close enough then try to find click location
        else:
            sleep(1)
            if hover_destination(([149, 41, 98],[235, 101, 223]), "images/dur.png"):
                log.info("Entrance hovered")
                if exists("images/3.png",threshold=0.9):
                    log.info("Entering entrance")
                    pyag.click()
                else:
                    log.warning("Wrong entrance found.")
                    return False, get_meph_entrance_image(minimap)

                if exists("images/indurance3.png", 5, region=(2162,109,386,39),threshold=0.9):
                    log.info("Destination entered correctly.")
                    return True, None
                else:
                    log.info("Failed to enter durance level 3.")
                    return False, None
            else:
                log.error("Cannot find durance description of entrance")
        timeout_counter += 1


# TASKS - DONE
def find_meph_level():
    log.info("Find meph tele direction.")
    sleep(3)
    pyag.press(TELEPORT_KEY)
    teleport_to("tl", 600)
    teleport_to("dr", 600)
    teleport_to("dr", 600)
    teleport_to("tl", 600)
    teleport_to("tr", 600)
    teleport_to("dl", 600)
    teleport_to("dl", 600)
    teleport_to("tr", 600)

    minimap = get_screen(part=MINIMAP_REGION)
    log.info(str(get_char_location(minimap)))
    meph_map_masked, meph_map_target = get_meph_map(minimap,mode="shore")
    start_direction = get_meph_start_direction(meph_map_masked, minimap)
    log.info("Start direction is " + start_direction)

    meph_map_masked, meph_map_target = get_meph_map(minimap, mode="full")
    current_direction = start_direction
    tele_number = 0
    blocked = 0
    changed = 0
    last_moves = []
    known_entrance = None
    while True:
        tele_number += 1
        log.debug("Start teleporting number " + str(tele_number))
        log.info("Last moves: " + str(last_moves[-30:]))

        # Check if character stuck in loop
        last10 = last_moves[-10:]
        last50 = last_moves[-50:]
        if len([last10 for idx in range(len(last50)) if last50[idx : idx + len(last50)] == last10]) > 3:
            log.error("Character stuck. Trying some random teleports.")

        if tele_number >= 1000:
            log.error("Timout when teleporting.")
            raise GameError("Timout when teleporting.")

        #teleport_to(current_direction,800,sleep_time=0.15)
        teleport_to(current_direction,600,sleep_time=0.3,mode="continous")
        sleep(0.18)

        old_minimap, old_meph_map_masked, old_meph_map_target = minimap, meph_map_masked, meph_map_target
        log.debug("Getting new minimap")
        minimap = get_screen(part=MINIMAP_REGION)
        log.visual(
        VisualRecord("New minimap", [minimap], fmt="png"))
        log.debug("Minimap transformation")
        meph_map_masked, meph_map_target = get_meph_map(minimap, mode="full")

        if get_entrance_location(known_entrance, minimap) != (None,None):
            entrance_result, known_entrance = goto_entrance()
            if entrance_result:
                log.info("Mephisto level found.")
                break
        else:
            #current_direction, blocked, changed, last_moves = find_new_direction(current_direction, meph_map_masked, old_meph_map_masked, blocked, changed, last_moves)
            current_direction, last_moves = find_new_direction2(current_direction, meph_map_masked, old_meph_map_masked, last_moves)

# TASKS DONE
def meph_bait():
    sleep(0.3)
    go_to_destination(([170, 39, 82],[186, 75, 175]),(-85,-40),filter=True, accepted_distance=10, button="right")
    sleep(0.7)
    go_to_destination(([170, 39, 82], [186, 75, 175]), (-85, 0), filter=True, accepted_distance=10)
    sleep(0.7)
    go_to_destination(([170, 39, 82], [186, 75, 175]), (-50, 30), filter=True, accepted_distance=10, button="right")
    sleep(1)
    go_to_destination(([170, 39, 82], [186, 75, 175]), (-48, 50), filter=True, accepted_distance=7, move_sleep=0.7,move_step=(60,100))

# TASKS DONE
def go_to_mephisto():
    for i in range(1,9):
        teleport_to("tl", 800, sleep_time=0.3,offset=(0,450))
    meph_bait()

def kill_mephisto():
    pass

####### TESTS


def hover_test(image,special_shift):
    diff_location_x, diff_location_y = get_diff_from_destination(image)
    center_x, center_y = CENTER_LOCATION
    log.info("diff_location_x: {} diff_location_y: {}".format(diff_location_x,diff_location_y))
    special_shift_x, special_shift_y = special_shift
    checking_location = (center_x + (diff_location_x * 15) + special_shift_x, center_y + (diff_location_y * 16)+ special_shift_y)
    hover(checking_location)


### MAP STICHING TEST
def map_stiching():
    sleep(3)
    minimaps = []
    for i in range(1,5):
        log.info("Stiching minimap nr " + str(i))
        minimap = get_screen(part=MINIMAP_REGION)
        meph_map_masked, meph_map_target = get_meph_map(minimap, mode="full")
        meph_map_masked = cv.cvtColor(meph_map_masked,cv.COLOR_GRAY2RGB)
        minimaps.append(meph_map_masked)
        sleep(2)

    sticher = cv.Stitcher_create()
    status,full_map = sticher.stitch(minimaps)
    cv.imshow("stitched map", full_map)
    cv.imshow("all maps", np.hstack(minimaps))
    cv.waitKey()


# Image clasifier
#from vision import Vision
#from time import time
#from windowcapture import WindowCapture
# def image_clasifier():
#     # load the trained model
#     cascade_limestone = cv.CascadeClassifier('meph.xml')
#     # load an empty Vision class
#     vision_limestone = Vision(None)
#
#     # initialize the WindowCapture class
#     wincap = WindowCapture('Albion Online Client')
#
#     loop_time = time()
#     while(True):
#
#         # get an updated image of the game
#         screenshot = wincap.get_screenshot()
#
#         # do object detection
#         #rectangles = cascade_limestone.detectMultiScale(screenshot)
#
#         # draw the detection results onto the original image
#         #detection_image = vision_limestone.draw_rectangles(screenshot, rectangles)
#
#         # display the images
#         cv.imshow('Unprocessed', screenshot)
#
#         # debug the loop rate
#         print('FPS {}'.format(1 / (time() - loop_time)))
#         loop_time = time()
#
#         # press 'q' with the output window focused to exit.
#         # press 'f' to save screenshot as a positive image, press 'd' to
#         # save as a negative image.
#         # waits 1 ms every loop to process key presses
#         key = cv.waitKey(1)
#         if key == ord('q'):
#             cv.destroyAllWindows()
#             break
#         elif key == ord('f'):
#             cv.imwrite('positive/{}.jpg'.format(loop_time), screenshot)
#         elif key == ord('d'):
#             cv.imwrite('negative/{}.jpg'.format(loop_time), screenshot)
#
#     print('Done.')


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

get_pixels("images/char_colors2.png")
exit(0)
#colors_checker()
#while True:
#    minimap = get_screen(part=MINIMAP_REGION)

#sleep(2)
minimap = get_screen(part=MINIMAP_REGION)
meph_map_masked, meph_map_target = get_meph_map(minimap, mode="full")
# get_entrance_location(None, minimap)
# exit(0)
#find_new_terain(meph_map_masked, "tl")
#check_direction(meph_map_masked, "dr",  type="wall")
#find_line(meph_map_masked, direction="tl", type="terain")
find_meph_level()
go_to_mephisto()
#meph_bait()
#image_clasifier()
exit(0)

#find_external_points(minimap)
# exit(0)

# contours, hierarchy = cv.findContours(meph_map_masked, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
# meph_map_masked = cv.cvtColor(meph_map_masked, cv.COLOR_GRAY2BGR)
# m1 = meph_map_masked.copy()
# m2 = meph_map_masked.copy()
# cv.drawContours(m1, contours, -1, (0,255,0), 5)
# cv.drawContours(m2, contours, -3, (0,255,0), 5)
# cv.imshow("Cleared Map", np.hstack([meph_map_masked, m1, m2]))
# cv.waitKey(0)




# Copy edges to the images that will display the results in BGR
# map_lined = cv.cvtColor(meph_map_masked, cv.COLOR_GRAY2BGR)
# map_lined_normal = map_lined.copy()
#
# map_blured = cv.GaussianBlur(map_lined_normal,(9,9),0)
#
# thresh, map_blured = cv.threshold(map_blured,50,255,cv.THRESH_BINARY)
# map_blured_gray = cv.cvtColor(map_blured, cv.COLOR_BGR2GRAY)
#
# cnts = cv.findContours(map_blured_gray.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
# cnts = imutils.grab_contours(cnts)
# log.info(str(cnts))
# c = max(cnts, key=cv.contourArea)
# extLeft = tuple(c[c[:, :, 0].argmin()][0])
# extRight = tuple(c[c[:, :, 0].argmax()][0])
# extTop = tuple(c[c[:, :, 1].argmin()][0])
# extBot = tuple(c[c[:, :, 1].argmax()][0])
# cv.drawContours(map_blured, [c], -1, (0, 255, 255), 2)
# cv.circle(map_blured, extLeft, 8, (0, 0, 255), -1)
# cv.circle(map_blured, extRight, 8, (0, 255, 0), -1)
# cv.circle(map_blured, extTop, 8, (255, 0, 0), -1)
# cv.circle(map_blured, extBot, 8, (255, 255, 0), -1)

#map_blured = cv.cvtColor(map_blured, cv.COLOR_GRAY2BGR)

#map_canny = cv.Canny(map_blured, 30, 300, None, 3)

# def change_bar(val):
#     map_blured = cv.GaussianBlur(map_lined_normal, (val, val), 0)
#     cv.imshow("window_name", map_blured)
#
# cv.imshow("window_name", map_blured)
# cv.createTrackbar('blur', "window_name", 0, 500, change_bar)
# cv.waitKey(0)

# lines = cv.HoughLines(map_canny, 1, np.pi / 180, 150, None, 0, 0)
#
# if lines is not None:
#     for i in range(0, len(lines)):
#         rho = lines[i][0][0]
#         theta = lines[i][0][1]
#         a = math.cos(theta)
#         b = math.sin(theta)
#         x0 = a * rho
#         y0 = b * rho
#         pt1 = (int(x0 + 1000 * (-b)), int(y0 + 1000 * (a)))
#         pt2 = (int(x0 - 1000 * (-b)), int(y0 - 1000 * (a)))
#         cv.line(map_lined_normal, pt1, pt2, (0, 0, 255), 3, cv.LINE_AA)

# linesP = cv.HoughLinesP(meph_map_masked, 1, np.pi / 180, 10, None, 10, 10)
#
# if linesP is not None:
#     for i in range(0, len(linesP)):
#         l = linesP[i][0]
#         cv.line(map_lined, (l[0], l[1]), (l[2], l[3]), (0, 0, 255), 3, cv.LINE_AA)
#
#
# def change_bar(val):
#     meph_map_masked_copy = meph_map_masked.copy()
#     linesP = cv.HoughLinesP(meph_map_masked_copy, 1, np.pi / 180, 35, None, 20, 10)
#     map_lined_copy = map_lined_normal.copy()
#     meph_map_masked_copy = cv.cvtColor(meph_map_masked_copy, cv.COLOR_GRAY2BGR)
#     if linesP is not None:
#         for i in range(0, len(linesP)):
#             l = linesP[i][0]
#             cv.line(meph_map_masked_copy, (l[0], l[1]), (l[2], l[3]), (0, 0, 255), 3, cv.LINE_AA)
#             log.info("Line number " + str(i) + str(l))
#     cv.imshow(window_name, meph_map_masked_copy)
#
# window_name = "map"
# cv.imshow(window_name, map_lined)
# cv.createTrackbar('min', window_name, 0, 500, change_bar)
# cv.waitKey(0)

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

# LOOT COLLECTOR
good_items = {}
# Load items lists
for item_rarity in ["unique","set","rune","magic"]:
    with open("items/" + item_rarity + ".txt") as file:
        file_lines = [line.rstrip() for line in file]
        good_items[item_rarity] = [re.sub(r"(\w)([A-Z])", r"\1 \2", line.split(" ")[2]) for line in file_lines if line.startswith("[Name]")]
        log.info("Item rarity {}:".format(item_rarity))
        log.info(good_items[item_rarity])

# D2CV
# Main loop
while game_number < games_max:
    try:
        game_number += 1
        potioner_thread = None
        # STATISTICS
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
            sleep(95 - game_time.total_seconds())
            log.info("Game took: " + str(game_time.seconds))
            continue
    except Exception as e:
        log.error(e, exc_info=True)
        log.exception('Game crashed. Restoring it')
        issues_counter += 1
        issues_list.append(e)
        game_restore()