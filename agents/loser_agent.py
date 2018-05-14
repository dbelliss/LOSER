# https://chatbotslife.com/building-a-basic-pysc2-agent-b109cde1477c
from pysc2.agents import base_agent
from pysc2.lib import actions
from pysc2.lib import features
from pprint import pprint
from time import gmtime, strftime, localtime
import os

import time

# Functions
_NOOP = actions.FUNCTIONS.no_op.id
_SELECT_POINT = actions.FUNCTIONS.select_point.id
_RALLY_UNITS_MINIMAP = actions.FUNCTIONS.Rally_Units_minimap.id
_SELECT_ARMY = actions.FUNCTIONS.select_army.id
_ATTACK_MINIMAP = actions.FUNCTIONS.Attack_minimap.id

BUILD_SPAWNING_POOL = actions.FUNCTIONS.Build_SpawningPool_screen.id
TRAIN_OVERLORD = actions.FUNCTIONS.Train_Overlord_quick.id
TRAIN_DRONE = actions.FUNCTIONS.Train_Drone_quick.id
TRAIN_ZERGLING = actions.FUNCTIONS.Train_Zergling_quick.id
SELECT_LARVA = actions.FUNCTIONS.select_larva.id

# Features
_PLAYER_RELATIVE = features.SCREEN_FEATURES.player_relative.index
_UNIT_TYPE = features.SCREEN_FEATURES.unit_type.index

# Unit IDs
HATCHERY = 86
CREEP_TUMOR = 87
EXTRACTOR = 88
SPAWNING_POOL = 89
EVOLUTION_CHAMBER = 90
HYDRALISK_DEN = 91
SPIRE = 92
ULTRALISK_CAVERN = 93
INFESTATION_PIT = 94
NYDUS_NETWORK = 95
BANELING_NEST = 96
ROACH_WARREN = 97
SPINE_CRAWLER = 98
SPORE_CRAWLER = 99
LAIR = 100
HIVE = 101
GREATER_SPIRE = 102
EGG = 103
DRONE = 104
ZERGLING = 105
OVERLORD = 106
HYDRALISK = 107
MUTALISK = 108
ULTRALISK = 109
ROACH = 110
INFESTOR = 111
CORRUPTOR = 112
BROOD_LOAD_COCOON = 113
BROOD_LORD = 114
BANELING_BURROWED = 115
DRONE_BURROWED = 116
HYDRALISK_BURROWED = 117
ROACH_BURROWED = 118
ZERGLING_BURROWED = 119
INFESTOR_TERRAN_BURROWED = 120
QUEENBURROWED = 125
QUEEN = 126
INFESTOR_BURROWED = 127
OVERLORD_COCOON = 128
OVERSEER = 129
LARVA = 151

INFESTOR_TERRAN = 7
BANELING_COCOON = 8
BANELING = 9
CHANGELING = 12
CHANGELING_ZEALOT = 13
CHANGELING_MARINE_SHIELD = 14
CHANGELING_MARINE = 15
CHANGELING_ZERGLING = 16


# Parameters
_PLAYER_SELF = 0
_NUM_MINERALS = 1
_NUM_VESPENE = 2
_SUPPLY_MAX = 4
_SUPPLY_USED = 3
_ARMY_SUPPLY = 5
_WORKER_SUPPLY = 6
_IDLE_WORKERS = 7
_ARMY_COUNT = 8
_WARP_GATE_COUNT = 9
_LARVA_COUNT = 10


_NOT_QUEUED = [0]
_QUEUED = [1]

class LoserAgent(base_agent.BaseAgent):
    base_top_left = None
    overlord_built = False
    larva_selected = False
    drone_selected = False
    spawning_pool_built = False
    spawning_pool_selected = False
    spawning_pool_rallied = False
    army_selected = False
    army_rallied = False

    def __init__(self, is_logging = False):
        super().__init__()

        # For debugging
        self.is_logging = is_logging
        self.step_num = 0
        if self.is_logging:

            # Make logs directory if it doesn't exist
            if not os.path.exists("./logs"):
                os.mkdir("./logs")
            self.log_file_name = "./logs/" + strftime("%Y-%m-%d %H:%M:%S", localtime())
            self.log_file = open(self.log_file_name, "w+")  # Create log file based on the time

        # Observation
        self.obs = None  # cur observations, step in step function

        # Constants
        self.researched = 2  # If an upgrade has been research
        self.is_researching = 1  # If an upgrade is being researched
        self.not_researched = 0  # If an upgrade is not being researched and has not been researched

        # Number of ground unit types
        self.num_queens = None  # number of queens
        self.num_zergling = None  # number of zergling
        self.num_banelings = None  # number of banelings
        self.num_roaches = None  # number of roaches
        self.num_hydralisks = None  # number of hydralisks
        self.num_swarm_hosts = None  # number of swarm hosts
        self.num_ravagers = None  # number of ravagers
        self.num_lurkers = None  # number of lurkers
        self.num_infestors = None  # number of infestors
        self.num_ultralisks = None  # number of ultralisks
        self.num_changelings = None  # number of changelings

        # Number of flying unit types
        self.num_overlords = None  # number of overlords
        self.num_overseers = None  # number of overseers
        self.num_mutalisks = None  # number of mutalisks
        self.num_corruptors = None  # number of corruptors
        self.num_brood_lords = None # number of brood lords
        self.num_vipers = None  # number of vipers


        # non-standard upgrades purchased
        self.can_burrow = None # true if Burrow has been purchased
        self.zergling_speed = None # True if Metabolic Boost has been purchased
        self.zergling_attack_boost = None  # True if Adrenal glands has been purchased
        self.baneling_speed = None # True if Centrifugal Hooks has been purchased
        self.roach_speed = None  # True if Glial Reconstruction has been purchased
        self.roach_tunnel = None  # True if Tunneling Claws reconstruction has been purchased
        self.overlord_speed = None  # True if Pneumatized Carapace has been purchsed
        self.hydralisk_range = None  # True if Grooved Spines has been purchased
        self.infestor_parasite = None  # True if Neural parasite has been purchased
        self.infestor_energy = None  # True if Pathogen Glands has been purchased
        self.ultralisk_defense = None  # True if Chitinous Plating has been purchased

        # standard upgrades
        # TODO

    def step(self, time_step):
        self.step_num += 1
        self.obs = time_step.observation
        super().step(time_step)
        self.log("Step: " + str(self.step_num))
        self.log("Minerals: " + str(self.cur_minerals))
        self.log("Vespene: " + str(self.cur_vespene))
        self.log("Cur Supply: " + str(self.cur_supply))
        self.log("Max Supply: " + str(self.max_supply))
        self.log("Num drones: " + str(self.num_drones))
        self.log("Num larva: " + str(self.num_larva))  # This is still a little buggy
        return actions.FunctionCall(_NOOP, [])

    def ResetBeliefState(self):
        pass

    @property
    def cur_minerals(self):
        """Get the current amount of minerals"""
        return self.obs["player"][_NUM_MINERALS]

    @property
    def cur_vespene(self):
        """Get the current amount of vespene"""
        return self.obs["player"][_NUM_VESPENE]


    @property
    def cur_supply(self):
        """Get the current amount of supply"""
        return self.obs["player"][_SUPPLY_USED]

    @property
    def max_supply(self):
        """Get the max supply"""
        return self.obs["player"][_SUPPLY_MAX]

    @property
    def num_drones(self):
        """Get the current amount of drones"""
        return self.obs["player"][_WORKER_SUPPLY]

    @property
    def num_larva(self):
        """Get the current amount of larva"""
         # FIXME: does not seem to work as expected
        return self.obs["player"][_LARVA_COUNT]

    def log(self, data):
        """Log the data to the logfile if this agent is set to log information and logfile is below 1 megabyte"""
        if self.is_logging and os.path.getsize(self.log_file_name) < 1000000:
            self.log_file.write(data + "\n")