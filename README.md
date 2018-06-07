# L.O.S.E.R. (Learning Operational Strategy Electing Robot)
A Starcraft 2 AI

## Setup
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

### Testing
`python3.6 examples/cannon_rush.py`

### Current issues:
* Error messages printing with certain operations like building extractors
* Moving the camera around in game has a chance to crash the agent

## Notes
* All agents derive from the base LoserAgent class
* The agent that swaps between other agents is AgentSelector

