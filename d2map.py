#
# Todo: Class D2map
#
#

from __future__ import print_function
from functools import reduce
import cv2 as cv
import numpy as np
import random as rng
import os
import pyautogui as pyag
import time
from d2sikuli import *
import ctypes
import imutils

rng.seed(12345)
user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

move_directions = {
    "t" : (1300, 10),
    "d" : (1300, 1100),
    "r" : (2550, 700),
    "l" : (10, 700),
    "tl" : (10, 10),
    "tr" : (2550, 10),
    "dl" : (10, 1100),
    "dr" : (2550, 1100)
}

def get_contours(gray_image,val):
    threshold = val
    # Detect edges using Canny
    canny_output = cv.Canny(gray_image, threshold, threshold * 2)
    # Find contours
    contours, hierarchy = cv.findContours(canny_output, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    # Draw contours
    drawing = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)
    for i in range(len(contours)):
        #color = (rng.randint(0,256), rng.randint(0,256), rng.randint(0,256))
        color = (256,256,256)
        cv.drawContours(drawing, contours, i, color, 2, cv.LINE_8, hierarchy, 0)
    # Show in a window
    drawing = cv.blur(drawing, (5, 5))
    return drawing
    #cv.imshow('Contours', drawing)


def get_screen(part=None,color_space=cv.COLOR_RGB2BGR):
    if part == "minimap":
        region = (0, 160, 672, 436)
    elif part == "belt":
        region = (1330,1348,299,78)
    elif part == "merc":
        region = (24,21,95,122)
    elif part:
        region = part

    if part:
        screen = pyag.screenshot(region=region)
    else:
        screen = pyag.screenshot()
    screenshot_clean = cv.cvtColor(np.array(screen), color_space)
    #cv.imshow("screenshot clean",  screenshot_clean)
    #cv.waitKey(0)
    return screenshot_clean


def multimask(image,mask_colors):
    #mask_colors = ([130,130,130],[136,136,136],[142,142,142],[123,142,161], [154,154,154])
    masks_list = []
    for mask_color in mask_colors:
        mask_array = np.array(mask_color, dtype = "uint8")
        new_mask = cv.inRange(image, mask_array, mask_array)
        masks_list.append(new_mask)

    final_mask = masks_list[0]
    for mask in masks_list:
        final_mask = final_mask | mask

    output = cv.bitwise_and(image, image, mask=final_mask)

    #cv.imshow("image masked",  output)
    #cv.waitKey(0)
    return output


def put_mask(image,mask_color):
    mask_array = np.array(mask_color, dtype="uint8")
    new_mask = cv.inRange(image, mask_array, mask_array)
    output = cv.bitwise_and(image, image, mask=new_mask)
    #cv.imshow("image masked",  output)
    #cv.waitKey(0)
    return output


def image_mask(image,region=None,inverted=False):
    log.debug("Image mask start.")
    best_location, result, screenshot = match(image, region=region)
    locations = np.where(result >= 0.7)
    locations = list(zip(*locations[::-1]))

    img = cv.imread(image, cv.IMREAD_UNCHANGED)
    image_size_w, image_size_h, image_size_c = img.shape
    size = (image_size_w, image_size_h)

    # Draw best location
    for location in locations:
        top_left = location
        bottom_right = (location[0] + size[1], location[1] + size[0])
        cv.rectangle(screenshot, top_left, bottom_right, color=(255, 255, 255), thickness=-1, )

    src_gray = cv.cvtColor(screenshot, cv.COLOR_BGR2GRAY)
    src_gray = cv.blur(src_gray, (5, 5))
    thresh = cv.threshold(src_gray, 150, 255, cv.THRESH_BINARY)[1]
    thresh = cv.erode(thresh, None, iterations=3)
    final = cv.dilate(thresh, None, iterations=3)
    if inverted:
        final = cv.bitwise_not(final)

    #cv.imshow("All locations", final)
    #cv.waitKey()

    return final


def get_easy_map(map, char_location):
    log.debug("Start getting transformed map.")
    image_maped = multimask(map,([130,130,130],[136,136,136],[142,142,142],[123,142,161], [154,154,154]))
    #d2map = cv.imread("images/screenexample.png", cv.IMREAD_UNCHANGED)[168:566,0:692]
    #d2map = cv.cvtColor(np.array(d2map), cv.COLOR_RGB2BGR)
    #image_maped = multimask(d2map,( [123,142,161], [130,130,130],[136,136,136],[142,142,142],[123,142,161], [154,154,154]))

    # Convert image to gray and blur it
    src_gray = cv.cvtColor(image_maped, cv.COLOR_BGR2GRAY)
    src_gray = cv.blur(src_gray, (4,4))
    src_gray = cv.blur(src_gray, (4, 4))

    scale_percent = 40  # percent of original size
    width = int(src_gray.shape[1] * scale_percent / 100)
    height = int(src_gray.shape[0] * scale_percent / 100)
    dim = (width, height)

    # resize image
    src_gray = cv.resize(src_gray, dim, interpolation=cv.INTER_AREA)


    max_thresh = 255
    thresh = 100 # initial threshold
    final_map = get_contours(src_gray, thresh)
    #cv.createTrackbar('Canny Thresh:', source_window, thresh, max_thresh, get_contours)
    #get_contours(thresh)
    #log.debug("Finish getting transformed map.")
    char_x, char_y = char_location
    char_x = round(char_x * scale_percent / 100)
    char_y = round(char_y * scale_percent / 100)
    log.debug("Scalled char loc: ({},{}).".format(char_x,char_y))
    cv.circle(final_map, (char_x, char_y), 5, (254, 148, 55), -1)
    #cv.putText(final_map, "char", (char_x - 25, char_y + 10), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    #cv.imshow("Final map", final_map)
    #cv.waitKey(0)
    return final_map

def get_object_location_by_color(map, color, color2=None):
    log.debug("Checking color {} possition on minimap.".format(color))
    mask_array = np.array(color, dtype="uint8")
    if color2 is not None:
        mask_array2 = np.array(color2, dtype="uint8")
    else:
        mask_array2 = np.array(color, dtype="uint8")
    mask = cv.inRange(map, mask_array, mask_array2)
    filtered_map = cv.bitwise_and(map, map, mask=mask)

    # convert the image to grayscale
    gray_image = cv.cvtColor(filtered_map, cv.COLOR_BGR2GRAY)

    #cv.imshow("Final map", gray_image)
    #cv.waitKey(0)

    # convert the grayscale image to binary image
    #ret, thresh = cv.threshold(gray_image, 127, 255, 0)

    # find contours in the binary image
    #contours, hierarchy = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

    #sorted_contours = sorted(contours, key=cv.contourArea, reverse=True)
    #if sorted_contours:
    #    biggest_contour = sorted_contours[0]
    #
    #    M = cv.moments(biggest_contour)
    #
    #    # calculate x,y coordinate of center
    #    cX = int(M["m10"] / M["m00"])
    #    cY = int(M["m01"] / M["m00"])
    #
    #    log.debug("Found best contour location: ({},{}).".format(cX, cY))
    #    return (cX, cY)
    #else:
    nonzero_points = cv.findNonZero(gray_image)
    if nonzero_points is None:
        return None,None
    middle_point = tuple(nonzero_points[round(len(nonzero_points)/2)][0])
    log.debug("Found color locations nr: {}. Choosen middle location: {}, type: {}".format(len(nonzero_points),middle_point,type(middle_point)))
    return middle_point


def get_tele_location(current_loc,destination_loc):
    log.info("screensize: " + str(screensize))
    current_x, current_y = current_loc
    destination_x, destination_y = destination_loc
    # top
    if (abs(current_x - destination_x) < 40) and (current_y - destination_y > 30):
        tele_loc = move_directions["t"]
    # down
    elif (abs(current_x - destination_x) < 40) and (current_y - destination_y < -30):
        tele_loc = move_directions["d"]
    # right
    elif (current_x - destination_x < -40) and (abs(current_y - destination_y) < 30):
        tele_loc = move_directions["r"]
    # left
    elif (current_x - destination_x > 40) and (abs(current_y - destination_y) < 30):
        tele_loc = move_directions["l"]
    # top left
    elif (current_x - destination_x > 40) and (current_y - destination_y > 30):
        tele_loc = move_directions["tl"]
    # top right
    elif (current_x - destination_x < -40) and (current_y - destination_y > 30):
        tele_loc = move_directions["tr"]
    # down left
    elif (current_x - destination_x > 40) and (current_y - destination_y < -30):
        tele_loc = move_directions["dl"]
    # down right
    elif (current_x - destination_x < -40) and (current_y - destination_y < -30):
        tele_loc = move_directions["dr"]

    return tele_loc


def minimap_to_game_location(current_loc,destination_loc):
    default_x = 1465
    default_y = 515
    point_step = 20

    current_x, current_y = current_loc
    destination_x, destination_y = destination_loc

    return (default_x + ((destination_x - current_x) * point_step),default_y + ((destination_y - current_y) * point_step))

def get_map_difference(old_map,new_map):
    # Compare images
    map_diff = np.sum((old_map.astype("float") - new_map.astype("float")) ** 2)
    map_diff /= float(old_map.shape[0] * old_map.shape[1])
    log.debug("Difference is: " + str(map_diff))
    return map_diff


def get_color_location(colors,region=None):
    screen = get_screen(part=region)
    #cv.imshow("screen", screen)
    #cv.waitKey(0)
    masked_screen = multimask(screen,colors)


    #cv.imshow("masked",  masked_screen)
    #cv.waitKey(0)

    # convert the image to grayscale
    gray_image = cv.cvtColor(masked_screen, cv.COLOR_BGR2GRAY)

    # threshold the image, then perform a series of erosions + dilations to remove any small regions of noise
    thresh = cv.threshold(gray_image, 5, 255, cv.THRESH_BINARY)[1]

    # find contours in thresholded image, then grab the largest one
    cnts = cv.findContours(thresh.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    if not cnts:
        log.debug("Color not found.")
        return None,None

    c = max(cnts, key=cv.contourArea)

    item_x, item_y = tuple(c[c[:, :, 1].argmax()][0])
    item = item_x, item_y

    log.debug("Location found: " + str(item))
    return item

