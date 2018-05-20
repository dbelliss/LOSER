# https://chatbotslife.com/building-a-basic-pysc2-agent-b109cde1477c
import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer

from pprint import pprint
from time import gmtime, strftime, localtime
import os

# For debugging purposes only
import sys

# Get strategy enums
from strategies import Strategies

class LoserAgent(sc2.BotAI):
    base_top_left = None
    overlord_built = False
    larva_selected = False
    drone_selected = False
    spawning_pool_built = False
    spawning_pool_selected = False
    spawning_pool_rallied = False
    army_selected = False
    army_rallied = False

    def __init__(self, is_logging = False, is_printing_to_console = False):
        super().__init__()

        # For debugging
        self.is_logging = is_logging  # Setting this to true to write information to log files in the agents/logs directory
        self.is_printing_to_console = is_printing_to_console  # Setting this to true causes all logs to be printed to the console

        # Make logs directory if it doesn't exist
        if not os.path.exists("./logs"):
            os.mkdir("./logs")
        self.log_file_name = "./logs/" + strftime("%Y-%m-%d %H:%M:%S", localtime()) + ".log"
        self.log_file = open(self.log_file_name, "w+")  # Create log file based on the time

        # Constants
        self.researched = 2  # If an upgrade has been research
        self.is_researching = 1  # If an upgrade is being researched
        self.not_researched = 0  # If an upgrade is not being researched and has not been researched

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

    '''
    Base on_step function
    Will only do something if it is given a strategy_num
    '''
    async def on_step(self, iteration, strategy_num = -1):
        self.log("Step: %s Idle Workers: %s Overlord: %s" % (str(iteration), str(self.get_idle_workers), str(self.units(OVERLORD).amount)))
        self.log("Step: " + str(iteration))

        if strategy_num == -1:
            self.log("No given strategy")
        else:
            # Make sure given strategy num is valid
            if Strategies.has_value(strategy_num):
                # Valid strategy num, convert int into enum value
                strategy = Strategies(strategy_num)
                self.log("Strategy is " + str(strategy))

                # Call the proper strategy function
                self.perform_strategy(iteration, strategy)
            else:
                # Not valid strategy num
                self.log_error("Unknown strategy " + str(strategy_num))

    '''
    Calls the correct strategy function given the strategy enum value
    Strategy functions can be override in base classes
    '''
    def perform_strategy(self, iteration, strategy):

        # Attack
        if strategy == Strategies.HEAVY_ATTACK:
            self.heavy_attack(iteration)
        elif strategy == Strategies.MEDIUM_ATTACK:
            self.medium_attack(iteration)
        elif strategy == Strategies.LIGHT_ATTACK:
            self.light_attack(iteration)

        # Scouting
        elif strategy == Strategies.HEAVY_SCOUTING:
            self.heavy_scouting(iteration)
        elif strategy == Strategies.MEDIUM_SCOUTING:
            self.medium_scouting(iteration)
        elif strategy == Strategies.LIGHT_SCOUTING:
            self.light_scouting(iteration)

        # Defense
        elif strategy == Strategies.HEAVY_DEFENSE:
            self.heavy_defense(iteration)
        elif strategy == Strategies.MEDIUM_DEFENSE:
            self.medium_defense(iteration)
        elif strategy == Strategies.LIGHT_DEFENSE:
            self.light_defense(iteration)

        # Harass
        elif strategy == Strategies.HEAVY_HARASS:
            self.heavy_harass(iteration)
        elif strategy == Strategies.MEDIUM_HARASS:
            self.medium_harass(iteration)
        elif strategy == Strategies.LIGHT_HARASS:
            self.light_harass(iteration)

        # Unknown
        else:
            self.log("Unknown strategy was given: " + str(strategy))

    '''
    Send all combat units (including the queen) to a known enemy position
    Do NOT recall ever
    '''
    def heavy_attack(self, iteration):
        self.log("I AM IN HEAVY ATTACK")
        pass

    '''
    Send all combat units (including the queen) to a known enemy position
    Recall after a certain amuont of units die 
    '''
    def medium_attack(self, iteration):
        pass

    '''
    Attack a known enemy position, but if you get attacked, retreat back to base
    '''
    def light_attack(self, iteration):
        pass

    '''
    Send all military units out to different areas
    Die for knowledge
    '''
    def heavy_scouting(self, iteration):
        pass

    '''
    Send a good amount of military units out
    '''
    def medium_scouting(self, iteration):
        pass

    '''
    Send a couple of things out for scouting and pull back if damage is taken
    '''
    def light_scouting(self, iteration):
        pass

    '''
    Complete recall back to main base
    Build lots of static defenses
    Build lots of lurkers 
    '''
    def heavy_defense(self, iteration):
        pass

    '''
    Recall and distribute between main base and explansions
    Build some defensive structures and units
    '''
    def medium_defense(self, iteration):
        pass

    '''
    Distribute forces between main base and expansions
    Build a few defensive structures and units
    '''
    def light_defense(self, iteration):
        pass

    '''
    Build swarms hosts and harass with them
    Build mutalisks and harass with them
    If harass units are attacked, move to the next base
    '''
    def heavy_harass(self, iteration):
        pass

    '''
    TODO
    '''
    def medium_harass(self, iteration):
        pass

    '''
    If attacked pull back for a set time
    Only use harass units if you have them
    '''
    def light_harass(self, iteration):
        pass

    @property
    def get_minerals(self):
        """Get the current amount of minerals"""
        return self.minerals

    @property
    def get_vespene(self):
        """Get the current amount of vespene"""
        return self.vespene

    @property
    def get_remaining_supply(self):
        """Get remaining supply"""
        return self.supply_left

    @property
    def get_workers(self):
        """Get the current amount of drones"""
        return self.workers.amount

    @property
    def get_idle_workers(self):
        return self.workers.idle.amount

    @property
    def get_larva_num(self):
        """Get the current amount of larva"""
        return self.units(LARVA).amount

    '''
    Prints to console if self.is_printing_to_console
    Writes to log file if self.is_logging
    '''
    def log(self, data):
        """Log the data to the logfile if this agent is set to log information and logfile is below 1 megabyte"""
        if self.is_logging and os.path.getsize(self.log_file_name) < 1000000:
            self.log_file.write(data + "\n")
        if self.is_printing_to_console:
            print(data)

    def log_error(self, data):
        data = "ERROR: " + data
        self.log_file.write(data + "\n")
        print(data)


def main():
    # Start game with LoserAgent as the Bot, and begin logging
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Zerg, LoserAgent(True, True)),
        Computer(Race.Protoss, Difficulty.Medium)
    ], realtime=False)

if __name__ == '__main__':
    main()
