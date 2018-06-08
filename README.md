# L.O.S.E.R. (Learning Operational Strategy Electing Robot)
A Starcraft 2 AI

## Proposal and Report
[Here](./ProjectReport.pdf)

## Setup
This setup assumes you are using a machine running a Linux operating system

### Install Python Dependencies
pip3 install matplotlib
sudo apt-get install python3-tk

### Install pysc2
Install pysc2 from: 

### Install python-sc2 with Starcraft 2 Viewer
Install python-sc2 with starcraft viewer (We found that this works the best when you clone the repo to the following path: `~/StarCraftII/`: 

```
git clone https://github.com/dbelliss/python-sc2
cd python-sc2
sudo  python3.6 setup.py install
```
##### IMPORTANT SIDE NOTE
If you have already installed the Dentosal python-sc2 repository, go into the installed location and do the following before the above:

`sudo rm -rf sc2/`

### Testing the Installation
`python3.6 examples/cannon_rush.py`

### Current issues:
* Error messages printing with certain operations like building extractors
* Moving the camera around in game has a chance to crash the agent
* This bot is designed only for 1v1's with only a single enemy starting position

## How it Works
Our main agent is designed to choose one strategy from a pool of strategies (attack, defend, scout, harass), and one build from a pool of builds (For example Zergling and Baneling). After certain intervals of time, the agent will evaluate it's current fitness, and if it is below a certain threshold, it will input the game state (unit composition, enemy unit composition, minerals, vespene gas, etc.) into a a neural network to determine the next strategy it should choose, and input the same data into a different neural network to determine the build to use.

### LoserAgent
All of these classes derive from LoserAgent. Loser agent is the only agent that implements strategy functions. LoserAgent also has it's own build order, but this is only to quickly test the base agent.

### AgentSelector
AgentSelector is the agent that learns and swaps between strategies.

### Strategies
Possible strategies an agent can use are:
* Heavy Attack - Send all army units towards the enemy base, and whoever gets there first attacks
* Medium Attack - Send all army units towards the enemy base, but try to group some army units together before moving forward
* Light Attack - Send all army units towards th enemy base, but only advance towards the enemy base if almost all untis are together
* Heavy Scouting - Send out all army units to random locations
* Medium Scouting - Send out 50% of all army units to random locations
* Light Scouting - Send out 50% of all army units to random locations, and have a unit return to base if it is damaged
* Heavy Defense - Recall all army units to the main base and build 4 spinecrawlers, 4 sporecrawlers, and 10 lurkers 
* Medium Defense - Recall all army units to the main base and build 3 spinecrawlers, 3 sporecrawlers, and 5 lurkers 
* Light Defense - Recall all army units to the main base and build 1 spinecrawlers, 1 sporecrawlers, and 3 lurkers 
* Heavy Harass - Send mutalisks to attack the enemy's workers form the side, and attack with other army units
* Medium Harass - Send mutalisks to attack the enemy's workers form the side, attack with other army units, and return to base if damaged to 50% health
* Light Harass - Send mutalisks to attack the enemy's workers form the side, attack with other army units, and return to base if damaged at all

### Builds
Possible builds an agent can use are:
* Drone and Overlord
* Mutalisk and Zergling
* Roach and Hydralisk
* Hydralisk and Zergling
* Zergling and Baneling


