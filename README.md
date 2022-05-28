# <img src="assets/logo.png">
Diablo 2 Computer Vision bot based on OpenCV. Project created for educational purposes, is not maintained anymore and 
as well wasn't created to be supported on machines other than owned by creator, if you are looking for similar project 
check [Botty](https://github.com/aeon0/botty). In short - bot create new games in Diablo 2 game - do some actions in 
village and travel to some locations with monsters. Kills that monsters, check if some interesting items were dropped 
and if yes then collect them. To run bot check configuration section and run src/main.py.

https://github.com/narsdk/d2cv/blob/master/assets/d2cv-pindlerun.mp4

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

### Clicking on buttons

### Moving on map

### Using potions

### Collecting items

### Searching for an entrance to next location
