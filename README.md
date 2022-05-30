# <img src="assets/logo.png">
Diablo 2 Computer Vision bot based on OpenCV. Project created for educational purposes, is not maintained anymore and 
as well wasn't created to be supported on machines other than owned by creator, if you are looking for similar project 
check [Botty](https://github.com/aeon0/botty). In short - bot create new games in Diablo 2 game - do some actions in 
village and travel to some locations with monsters. Kills that monsters, check if some interesting items were dropped 
and if yes then collect them. To run bot check configuration section and run src/main.py.

Here example of single run with buying potions, storing items and ressurecting mercenary - including behaviour for some 
clicking failes due to NPC movement:

https://user-images.githubusercontent.com/61120673/170844156-fee9b8e0-7132-4045-aab8-6e18090005fd.mp4


## Flow & Features

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

## Configuration

### Game Configuration Notes

Large Font Mode: Enabled

Resolution: windowed 2556x1373

Minimap: on the left side

Language: English

## Some features explained

### Clicking on images
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

### Moving on map

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

We travel here as our real destination is portal near the Anya teleport. We want to enter it now:


```
Character.enter_destination(([0, 239, 239], [0, 243, 243]), "images/nihlak_portal.png", "images/ingame.png")

where:
([0, 239, 239], [0, 243, 243]) - HSV range of searched yellow color (cross on map displaying portal location)
"images/nihlak_portal.png" - after hover portal this image should appear
"images/ingame.png" - 


### Using potions

### Collecting items

### Searching for an entrance to next location
