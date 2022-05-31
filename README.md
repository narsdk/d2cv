# <img src="assets/logo.png">
Diablo 2 Ressurected Computer Vision bot based on OpenCV. Project created for educational purposes, is not maintained anymore and 
as well wasn't created to be supported on machines other than owned by creator, if you are looking for similar project 
check [Botty](https://github.com/aeon0/botty). In short - bot create new games in Diablo 2 game - do some actions in 
village and travel to some locations with monsters. Kills that monsters, check if some interesting items were dropped 
and if yes then collect them. To run bot check configuration section and run src/main.py.

Here example of single run with buying potions, storing items and ressurecting mercenary - including behaviour for some 
clicking failes due to NPC movement:

https://user-images.githubusercontent.com/61120673/170844156-fee9b8e0-7132-4045-aab8-6e18090005fd.mp4


# Flow & Features

- Games management - create new games, restart game during failes (like game crashes which are quite often),
- Move through city maps basing on minimap locations and targets,
- Buy potions from merchants to fullful potions belt,
- Store items found in previous game in stash with moving through all tabs and making sure that main tab has at least
  100k of gold for merchants,
- Resurrect mercenary in the right NPC, 
- Pickup hero corpse if he died in previous game,
- Task: Pindleskin - Go to Anya portal -> teleport near the Pindelskin -> Kill Pindelskin and all mobs -> Collect items 
  interesting items,
- Task: Mephisto - Go to "Durance of Hate Level 2" waypoint -> Travel through location using algorithm similar to used 
  by automatic vacuum cleaners and looking to correct entrance to next location -> Teleport to mephisto and make a bait 
  to kill him behind the lava river,
- Heal character and mercenary - using potions from belt if the resource is below a certain level,
- Statistics - show live statistics about current run in file including number of items found, some times statistics, 
  all issues etc,
- Logging - visual logger in html format - includes images during transformation what helps debug OpenCV issues. 

# Configuration

## Game Configuration Notes

Large Font Mode: Enabled

Resolution: windowed 2556x1373

Minimap: on the left side

Language: English

# Some features explained

## Clicking on images
To recognize what is happening on the screen and do some input actions like clicking I implemented [src/pysikuli.py with class Region](src/pysikuli.py). Naming of class, their functions and behaviours I did very similar to [SikuliX](http://sikulix.com/) which I used a lot in the past. So there is Region class which represents part of the screen (x,y, width, height and screenshot image). Most common flow is: 
1. Do screenshot of a part of the screen. My research confirmed that fastest library for that on Windows is [d3dshot](https://pypi.org/project/d3dshot/), in my case even 20 times faster than PIL.ImageGrab or screenshot function from PyAutoGUI.

![image](https://user-images.githubusercontent.com/61120673/170867751-42d2ae84-a7a4-4eb8-b239-7135c279c33c.png)

2. The core of Region are matching functions. I implemented matching a colors mask and images patterns. Take an image pattern:

![image](https://user-images.githubusercontent.com/61120673/170867862-f667783b-4e11-4117-a64d-a7003e233e02.png)

Use OpenCV matcher to find most similar areas on screenshot.

![image](https://user-images.githubusercontent.com/61120673/170867480-27ff90dc-9994-4cad-84b7-0a545d447cdc.png)

If similarity of some is higher than our threshold we have a match with some details like a center point.
![image](https://user-images.githubusercontent.com/61120673/170868364-2d8e174b-ca30-405b-8040-4a3b8a548946.png)

3. It clicks on center location of found object.

## Moving on map

[MapTraveler](src/maptraveler.py) class is responsible for our hero ([Character class](src/character.py)) moving from location to location. Steps are described in classes [TownManager](src/town_manager.py) and [Task](src/tasks.py) (both are a Strategy design patterns and represents towns from different game acts and different opponents to reach and kill). In example we want to move to Anya NPC. We use some reference points from minimap:

MINIMAP                                                 // REFERENCE IMAGE //                             IMAGE FOUND ON MINIMAP

<img src=https://user-images.githubusercontent.com/61120673/170946032-c65dffc0-7d85-47e1-a5e2-21064f1619fe.png width="45%" height="45%"><img src=https://user-images.githubusercontent.com/61120673/170946194-123c62b2-2eb9-48e4-b33b-3e6c7e82c572.png width="10%" height="10%"><img src=https://user-images.githubusercontent.com/61120673/170946234-b898afc6-8f42-4c9b-b463-87ade2b458af.png width="45%" height="45%">

On our way there are some obstacles (building) so we uses two moves:

```
Character.go_to_destination("images/anya.png", shift=(100, 40))
Character.go_to_destination("images/anya.png", shift=(20, 45), move_step=(400, 450))
```
shift parameters means that our destination is (x,y) pix shifted from found destination image. So that two steps will be something like:

![minimap1](https://user-images.githubusercontent.com/61120673/170951556-ff916fe4-f46b-48d6-95d9-08d597a4194c.png)

Our real destination is portal near the Anya. We want to enter it now:


```
Character.enter_destination(([0, 239, 239], [0, 243, 243]), "images/nihlak_portal.png", "images/ingame.png")
```

where:
([0, 239, 239], [0, 243, 243]) - HSV range of searched yellow color (cross on map displaying portal location)
"images/nihlak_portal.png" - after hover portal by mouse cursor this image should appear - ![image](https://user-images.githubusercontent.com/61120673/171049986-6e93045b-5cdb-42d6-b13e-7cd4a361f998.png)
. When it appear then we click left mouse button.
"images/ingame.png" - check if character moved to other location successfully.


## Using potions

Instance of class [Potioner](src/potioner.py) is started as a separate thread and checking for an amount of life and mana resources of hero and mercenary. It takes region of resource bar, filter it by resource color and check most extreme points of counturs - in case of hero life it will be a most extreme top value, in case of mercenary life it will be a most extreme right. They are represented by grey dots on last processed images:

![image](https://user-images.githubusercontent.com/61120673/171055719-c7d9c153-e1f5-4382-b775-7691b2a9d852.png)

here calculated amount of life is 30%

![image](https://user-images.githubusercontent.com/61120673/171055770-bbd6da80-0c17-4e93-a3e3-e80e516eb5d7.png)

here calculated amount of mercenary life is 100%

## Collecting items

After killing opponents bot checks if there are some items to loot. In current implementation I used easy and not best solution - we are looking for a texts of some colors to collect items of unique/set quality (gold/green) or runes (orange). 


<img src=https://user-images.githubusercontent.com/61120673/171117662-d41c5eee-9b6e-40b8-8f76-1ca232a809e0.png width="50%" height="50%"><img src=https://user-images.githubusercontent.com/61120673/171117695-5651035d-b88c-4d50-a8a0-cda76fe035fa.png width="50%" height="50%">


It could be done much better using OCR like Tesseract. I use Tesseract when decide if item should be stored in stash. First we need to localize items to check in character equipment, I'm doing it by selecting all places which are not empty:

<img src=https://user-images.githubusercontent.com/61120673/171120400-a9d76a26-7593-49c9-a206-24582b83e1eb.png width="35%" height="35%">  <img src=https://user-images.githubusercontent.com/61120673/171120465-ab9c14cf-786b-4a75-86b0-aee61457db61.png width="35%" height="35%">

Prepare item description image to be easy to analize by OCR. First we have to get item description region, then we have to gather text contours:

<img src=https://user-images.githubusercontent.com/61120673/171121531-f58f28a6-08d1-4bc5-b230-82e7a7bf1834.png width="25%" height="25%"><img src=https://user-images.githubusercontent.com/61120673/171121937-7b420023-1177-4ba7-a58f-51f3e86055ec.png width="25%" height="25%"><img src=https://user-images.githubusercontent.com/61120673/171122156-8c595dd7-afc1-4dc9-9df4-b9481995b5b2.png width="25%" height="25%"><img src=https://user-images.githubusercontent.com/61120673/171122193-2781cc5d-3d82-4e99-bd61-29ace79bbd2a.png width="25%" height="25%">

We put characters contours to OCR and get "Um RUNE", item color is orange so we know that its type is "rune". Now we have to check if that item should be stored - by checking if its on [list of runes to store described in configuration files](items). I use items lists from old Diablo 2 bot called Etal Bot.


## Searching for an entrance to next location

Traveling in Diablo 2 is teleporting from one waypoint and looking for an entrance to next location. In most areas entrance to next location is near the external wall so teleporting through wall is the best strategy. I used algorithm similar to this used by autonomic vacuum cleaners:
```
- Check if there is a space in front of you and a wall on your left side.
- If there is a wall on left and space in front then go forward
- if there are no wall on left and there is a space then turn left
- if there is a wall on left and wall on the front then turn right
- if character didnt changes its location since last move then its blocked - repeat and if still is blocked then turn right
- do all until you will find entrance colors on minimap
```
There are few other conditions in algorithm to make it working correclty, this are main.

https://user-images.githubusercontent.com/61120673/171133759-1d8a4ac7-6df0-49f2-aa96-d8cea61338e8.mp4

But how does bot know if conditions are meet? By analizing contours from minimap. First we need to make minimap more readable:

<img src=https://user-images.githubusercontent.com/61120673/171134987-5c34f8b8-1bfa-4753-8163-69f5c5ad189b.png width="33%" height="33%"><img src=https://user-images.githubusercontent.com/61120673/171135033-8e3f36da-e587-4979-b6ea-922806185c18.png width="33%" height="33%"><img src=https://user-images.githubusercontent.com/61120673/171135125-72c89596-6a8f-4017-a66a-0a53aeca52e9.png width="33%" height="33%">

We know where our character is located on minimap so we can just evaluate what is on his front/left sides:

![image](https://user-images.githubusercontent.com/61120673/171137800-75c3bc14-3e76-4803-995a-47c3bdf79a2b.png)
![image](https://user-images.githubusercontent.com/61120673/171137825-fadb1a0d-41c5-4952-893e-48351fbaf4a1.png)

Result? Go forward!

How does bot check if character is blocked? We compare new gathered minimap with old one.
How does bot make sure that entrance is correct? If bot find entrance to not desired location then it saves shapes of walls near location and ignores them during teleportation.

## Logging in OpenCV

Debuging Computer Vision programs very often requires to check what is going on images - screenshot and during processing. Displaying images all the time during execution is not comfortable. With help here comes [visual-logging](https://github.com/dchaplinsky/visual-logging) which save logs in html format with images included. I really recomend a lot!



